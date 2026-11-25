import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import logger
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.services.report_service import ReportService
from app.services.gmail_service import GmailService
from app.services.notification_service import NotificationService


class SchedulerService:
    _task: Optional[asyncio.Task] = None
    _running: bool = False

    @classmethod
    def start(cls):
        """Start the background scheduler task."""
        if not cls._running:
            cls._running = True
            cls._task = asyncio.create_task(cls._loop())
            logger.info("Report Scheduler background loop started.")

    @classmethod
    def stop(cls):
        """Stop the background scheduler task."""
        cls._running = False
        if cls._task:
            cls._task.cancel()
            logger.info("Report Scheduler background loop stopped.")

    @classmethod
    async def _loop(cls):
        """Periodic background evaluation loop (every 60 seconds)."""
        while cls._running:
            try:
                await cls.execute_due_schedules()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler execution loop: {e}")

            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break

    @classmethod
    async def execute_due_schedules(cls, db: Optional[Session] = None):
        """Query and execute any scheduled reports that have reached their trigger time."""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            now = datetime.now(timezone.utc)
            due_schedules = ReportRepository.get_due_schedules(db, now)

            for schedule in due_schedules:
                user = UserRepository.get_by_id(db, schedule.user_id)
                if not user:
                    continue

                logger.info(f"Executing scheduled report '{schedule.report_name}' for user {user.id}")
                try:
                    # 1. Generate the report document
                    fmt = "pdf" if schedule.report_format in ("pdf", "both") else "excel"
                    report = await ReportService.generate_report(
                        db=db,
                        user=user,
                        title=schedule.report_name,
                        report_format=fmt,
                        dataset_id=schedule.dataset_id
                    )

                    # 2. If recipients provided, send via Gmail
                    recipients = [r.strip() for r in schedule.recipients.split(",") if r.strip()]
                    if recipients:
                        try:
                            ext = "pdf" if fmt == "pdf" else "xlsx"
                            await GmailService.send_report_email(
                                db=db,
                                user=user,
                                recipients=recipients,
                                subject=schedule.email_subject,
                                body=schedule.email_body,
                                file_path=report.file_path,
                                attachment_name=f"{schedule.report_name.replace(' ', '_')}.{ext}"
                            )
                            ReportRepository.update_email_status(
                                db=db,
                                report_id=report.id,
                                user_id=user.id,
                                status="sent",
                                recipients=",".join(recipients),
                                subject=schedule.email_subject
                            )
                            schedule.last_status = "success"
                            NotificationService.create_notification(
                                db=db,
                                user_id=user.id,
                                category="schedule",
                                title=f"Scheduled Report Sent: {schedule.report_name}",
                                message=f"Your {schedule.frequency} report '{schedule.report_name}' was generated and emailed.",
                                resource_type="schedule",
                                resource_id=schedule.id,
                            )
                        except Exception as mail_err:
                            logger.error(f"Failed to email scheduled report {schedule.id}: {mail_err}")
                            schedule.last_status = f"Generated, mail failed: {str(mail_err)[:100]}"
                            NotificationService.create_notification(
                                db=db,
                                user_id=user.id,
                                category="email",
                                title=f"Scheduled Email Failed: {schedule.report_name}",
                                message=f"Report generated, but Gmail delivery failed: {str(mail_err)[:120]}",
                                resource_type="schedule",
                                resource_id=schedule.id,
                            )
                    else:
                        schedule.last_status = "success"
                        NotificationService.create_notification(
                            db=db,
                            user_id=user.id,
                            category="schedule",
                            title=f"Scheduled Report Ready: {schedule.report_name}",
                            message=f"Your {schedule.frequency} report '{schedule.report_name}' was generated.",
                            resource_type="schedule",
                            resource_id=schedule.id,
                        )
                except Exception as gen_err:
                    logger.error(f"Failed to execute scheduled report {schedule.id}: {gen_err}")
                    schedule.last_status = f"failed: {str(gen_err)[:100]}"

                # Compute next execution time
                schedule.last_run_at = now
                if schedule.frequency == "weekly":
                    schedule.next_run_at = now + timedelta(days=7)
                elif schedule.frequency == "monthly":
                    schedule.next_run_at = now + timedelta(days=30)
                else:
                    schedule.next_run_at = now + timedelta(days=7)

                db.commit()
        finally:
            if should_close:
                db.close()

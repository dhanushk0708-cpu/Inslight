from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.report import Report, ScheduledReport


class ReportRepository:
    @staticmethod
    def create_report(
        db: Session,
        user_id: str,
        name: str,
        report_format: str,
        file_path: str,
        file_size: int,
        dataset_id: Optional[str] = None,
        parameters_json: Optional[str] = None,
        recipients: Optional[str] = None,
        email_subject: Optional[str] = None,
        status: str = "generated"
    ) -> Report:
        report = Report(
            user_id=user_id,
            dataset_id=dataset_id,
            name=name,
            report_format=report_format,
            file_path=file_path,
            file_size=file_size,
            parameters_json=parameters_json,
            recipients=recipients,
            email_subject=email_subject,
            status=status
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_by_id(db: Session, report_id: str, user_id: str) -> Optional[Report]:
        """Fetch report ensuring strict user ownership."""
        return db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()

    @staticmethod
    def get_user_reports(db: Session, user_id: str) -> List[Report]:
        """List all reports belonging to the user."""
        return db.query(Report).filter(Report.user_id == user_id).order_by(Report.created_at.desc()).all()

    @staticmethod
    def delete_report(db: Session, report_id: str, user_id: str) -> bool:
        """Delete report verifying ownership."""
        report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
        if not report:
            return False
        db.delete(report)
        db.commit()
        return True

    @staticmethod
    def update_email_status(
        db: Session,
        report_id: str,
        user_id: str,
        status: str,
        gmail_message_id: Optional[str] = None,
        recipients: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Optional[Report]:
        report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
        if not report:
            return None
        report.status = status
        if gmail_message_id:
            report.gmail_message_id = gmail_message_id
        if recipients:
            report.recipients = recipients
        if subject:
            report.email_subject = subject
        db.commit()
        db.refresh(report)
        return report

    # ━━━ Scheduled Reports ━━━
    @staticmethod
    def create_scheduled_report(
        db: Session,
        user_id: str,
        dataset_id: str,
        report_name: str,
        frequency: str,
        report_format: str,
        recipients: str,
        email_subject: str,
        email_body: str,
        next_run_at: datetime,
        is_active: bool = True
    ) -> ScheduledReport:
        schedule = ScheduledReport(
            user_id=user_id,
            dataset_id=dataset_id,
            report_name=report_name,
            frequency=frequency,
            report_format=report_format,
            recipients=recipients,
            email_subject=email_subject,
            email_body=email_body,
            next_run_at=next_run_at,
            is_active=is_active
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def get_scheduled_report(db: Session, schedule_id: str, user_id: str) -> Optional[ScheduledReport]:
        return db.query(ScheduledReport).filter(ScheduledReport.id == schedule_id, ScheduledReport.user_id == user_id).first()

    @staticmethod
    def get_user_scheduled_reports(db: Session, user_id: str) -> List[ScheduledReport]:
        return db.query(ScheduledReport).filter(ScheduledReport.user_id == user_id).order_by(ScheduledReport.created_at.desc()).all()

    @staticmethod
    def update_scheduled_report(
        db: Session,
        schedule_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[ScheduledReport]:
        schedule = db.query(ScheduledReport).filter(ScheduledReport.id == schedule_id, ScheduledReport.user_id == user_id).first()
        if not schedule:
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(schedule, k):
                setattr(schedule, k, v)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def delete_scheduled_report(db: Session, schedule_id: str, user_id: str) -> bool:
        schedule = db.query(ScheduledReport).filter(ScheduledReport.id == schedule_id, ScheduledReport.user_id == user_id).first()
        if not schedule:
            return False
        db.delete(schedule)
        db.commit()
        return True

    @staticmethod
    def get_due_schedules(db: Session, now: datetime) -> List[ScheduledReport]:
        return db.query(ScheduledReport).filter(
            ScheduledReport.is_active == True,
            ScheduledReport.next_run_at <= now
        ).all()

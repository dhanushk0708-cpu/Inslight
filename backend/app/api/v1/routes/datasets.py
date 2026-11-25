from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_optional_current_user, get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.services.audit_service import AuditService
from app.schemas.dataset import DatasetResponse, DatasetProfileResponse

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=dict)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Upload a CSV dataset, save it in user's isolated DuckDB storage, and profile statistics.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported.")

    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 100MB).")

    try:
        dataset, profile = DatasetService.save_and_register_dataset(
            db=db,
            user_id=user.id,
            file_bytes=content,
            filename=file.filename
        )
    except Exception as e:
        AuditService.log_action(db=db, user_id=user.id, action="dataset_upload", resource_type="dataset", status="failure", metadata={"filename": file.filename})
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV: {str(e)[:200]}. Ensure valid UTF-8/CSV formatting."
        )

    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="dataset_upload",
        resource_type="dataset",
        resource_id=dataset.id,
        status="success",
        metadata={"filename": file.filename, "rows": dataset.row_count, "columns": dataset.column_count},
    )
    return {
        "status": "success",
        "message": f"Loaded {dataset.row_count} rows with {dataset.column_count} columns",
        "dataset_id": dataset.id,
        "profile": profile
    }


@router.get("", response_model=List[DatasetResponse])
def list_user_datasets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all datasets owned by the authenticated user with columns."""
    datasets = DatasetRepository.get_user_datasets(db, user_id=user.id)
    output = []
    import json
    for d in datasets:
        cols = []
        if d.schema_metadata:
            try:
                meta = json.loads(d.schema_metadata)
                cols = [c.get("name") for c in meta.get("column_info", []) if c.get("name")]
            except Exception:
                pass
        item = DatasetResponse.model_validate(d)
        item.columns = cols
        output.append(item)
    return output


@router.get("/{dataset_id}/columns")
def get_dataset_columns(
    dataset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get columns for a specific dataset."""
    dataset = DatasetRepository.get_by_id(db, dataset_id=dataset_id, user_id=user.id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    cols = []
    if dataset.schema_metadata:
        try:
            import json
            meta = json.loads(dataset.schema_metadata)
            cols = [c.get("name") for c in meta.get("column_info", []) if c.get("name")]
        except Exception:
            pass
    if not cols:
        conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
        try:
            df_cols = conn.execute(f"DESCRIBE {dataset.table_name}").df()
            cols = df_cols["column_name"].tolist()
        finally:
            conn.close()
    return {"dataset_id": dataset_id, "columns": cols}


@router.get("/active", response_model=dict)
def get_active_dataset_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get profile of the active (most recently uploaded) dataset for user."""
    dataset = DatasetRepository.get_latest_for_user(db, user_id=user.id)
    if not dataset:
        # Load seed dataset if none exists for instant usability
        seed = DatasetService.load_seed_for_user(db, user_id=user.id)
        if seed:
            dataset, profile = seed
            return profile
        raise HTTPException(status_code=404, detail="No dataset loaded. Upload a CSV first.")

    import json
    profile = json.loads(dataset.schema_metadata) if dataset.schema_metadata else {}
    profile["id"] = dataset.id
    profile["dataset_id"] = dataset.id
    profile["table_name"] = dataset.table_name
    profile["original_filename"] = dataset.original_filename
    profile["filename"] = dataset.original_filename
    profile["row_count"] = dataset.row_count
    profile["rows"] = dataset.row_count
    profile["column_count"] = dataset.column_count
    profile["columns"] = dataset.column_count
    return profile


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a dataset ensuring strict ownership check."""
    success = DatasetRepository.delete(db, dataset_id=dataset_id, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found or unauthorized.")
    AuditService.log_action(db=db, user_id=user.id, action="dataset_delete", resource_type="dataset", resource_id=dataset_id, status="success")
    return {"message": "Dataset successfully deleted."}

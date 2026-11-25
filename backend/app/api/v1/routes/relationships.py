from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.schemas.phase3 import (
    RelationshipCandidatesRequest,
    RelationshipValidateRequest,
    RelationshipCreateRequest,
    RelationshipPreviewRequest,
    RelationshipResponse,
)
from app.services.relationship_service import DatasetRelationshipService

router = APIRouter(prefix="/relationships", tags=["Multi-Dataset Relational Intelligence"])


@router.post("/candidates")
def find_candidates(
    req: RelationshipCandidatesRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Detect matching foreign keys between two user datasets."""
    ds_src = DatasetRepository.get_by_id(db, req.source_dataset_id, user_id=user.id)
    ds_tgt = DatasetRepository.get_by_id(db, req.target_dataset_id, user_id=user.id)
    if not ds_src or not ds_tgt:
        raise HTTPException(status_code=404, detail="Source or target dataset not found or access denied.")

    conn_s = DatasetService.get_duckdb_connection(ds_src.storage_path, read_only=True)
    conn_t = DatasetService.get_duckdb_connection(ds_tgt.storage_path, read_only=True)
    try:
        return DatasetRelationshipService.detect_candidate_join_keys(
            conn_source=conn_s,
            source_table=ds_src.table_name,
            conn_target=conn_t,
            target_table=ds_tgt.table_name
        )
    finally:
        conn_s.close()
        conn_t.close()


@router.post("/validate")
def validate_relationship(
    req: RelationshipValidateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Assess key integrity, null rates, and relationship cardinality (1:1, 1:N, N:M)."""
    ds_src = DatasetRepository.get_by_id(db, req.source_dataset_id, user_id=user.id)
    ds_tgt = DatasetRepository.get_by_id(db, req.target_dataset_id, user_id=user.id)
    if not ds_src or not ds_tgt:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    conn_s = DatasetService.get_duckdb_connection(ds_src.storage_path, read_only=True)
    conn_t = DatasetService.get_duckdb_connection(ds_tgt.storage_path, read_only=True)
    try:
        return DatasetRelationshipService.validate_relationship(
            conn_source=conn_s,
            source_table=ds_src.table_name,
            conn_target=conn_t,
            target_table=ds_tgt.table_name,
            source_col=req.source_column,
            target_col=req.target_column
        )
    finally:
        conn_s.close()
        conn_t.close()


@router.post("/preview")
def preview_joined_records(
    req: RelationshipPreviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Execute preview cross-dataset join in DuckDB."""
    ds_src = DatasetRepository.get_by_id(db, req.source_dataset_id, user_id=user.id)
    ds_tgt = DatasetRepository.get_by_id(db, req.target_dataset_id, user_id=user.id)
    if not ds_src or not ds_tgt:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return DatasetRelationshipService.execute_joined_preview(
        source_db_path=ds_src.storage_path,
        source_table=ds_src.table_name,
        target_db_path=ds_tgt.storage_path,
        target_table=ds_tgt.table_name,
        source_col=req.source_column,
        target_col=req.target_column,
        limit=req.limit
    )


@router.post("", response_model=RelationshipResponse)
def save_relationship(
    req: RelationshipCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Persist verified dataset relationship."""
    ds_src = DatasetRepository.get_by_id(db, req.source_dataset_id, user_id=user.id)
    ds_tgt = DatasetRepository.get_by_id(db, req.target_dataset_id, user_id=user.id)
    if not ds_src or not ds_tgt:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    rel = DatasetRelationshipService.create_relationship(
        db=db,
        user_id=user.id,
        source_dataset_id=req.source_dataset_id,
        target_dataset_id=req.target_dataset_id,
        source_col=req.source_column,
        target_col=req.target_column,
        relationship_type=req.relationship_type
    )
    resp = RelationshipResponse.model_validate(rel)
    resp.source_dataset_name = ds_src.original_filename
    resp.target_dataset_name = ds_tgt.original_filename
    return resp


@router.get("", response_model=List[RelationshipResponse])
def list_relationships(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    rels = DatasetRelationshipService.list_relationships(db, user_id=user.id)
    result = []
    for r in rels:
        resp = RelationshipResponse.model_validate(r)
        if r.source_dataset:
            resp.source_dataset_name = r.source_dataset.original_filename
        if r.target_dataset:
            resp.target_dataset_name = r.target_dataset.original_filename
        result.append(resp)
    return result


@router.delete("/{rel_id}")
def delete_relationship(
    rel_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    success = DatasetRelationshipService.delete_relationship(db, user_id=user.id, rel_id=rel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship not found.")
    return {"status": "success", "message": "Relationship deleted."}

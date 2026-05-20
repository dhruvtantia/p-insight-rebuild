from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.uploads.schemas import (
    ColumnMappingRequest,
    ColumnMappingResponse,
    ColumnMappingSuggestionsResponse,
    ConfirmUploadResponse,
    UploadErrorsResponse,
    UploadJobResponse,
    ValidateUploadResponse,
)
from app.modules.uploads.service import UploadService

router = APIRouter(tags=["uploads"])


def get_upload_service(db: Annotated[Session, Depends(get_db)]) -> UploadService:
    return UploadService(db)


UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]


def require_upload_suggestions_enabled() -> None:
    require_feature_enabled("ENABLE_UPLOAD_SUGGESTIONS")


@router.post(
    "/api/portfolios/{portfolio_id}/uploads",
    response_model=UploadJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_upload(
    portfolio_id: str,
    user: CurrentUser,
    service: UploadServiceDep,
    file: UploadFile = File(...),
):
    return await service.create_upload(portfolio_id=portfolio_id, user=user, file=file)


@router.get("/api/uploads/{upload_job_id}", response_model=UploadJobResponse)
def get_upload(upload_job_id: str, user: CurrentUser, service: UploadServiceDep):
    return service.get_upload(upload_job_id=upload_job_id, user=user)


@router.post("/api/uploads/{upload_job_id}/column-mapping", response_model=ColumnMappingResponse)
def apply_column_mapping(
    upload_job_id: str,
    request: ColumnMappingRequest,
    user: CurrentUser,
    service: UploadServiceDep,
):
    return service.apply_column_mapping(
        upload_job_id=upload_job_id,
        user=user,
        mapping=request.mapping,
    )


@router.get("/api/uploads/{upload_job_id}/mapping-suggestions", response_model=ColumnMappingSuggestionsResponse)
def get_mapping_suggestions(
    upload_job_id: str,
    _: Annotated[None, Depends(require_upload_suggestions_enabled)],
    user: CurrentUser,
    service: UploadServiceDep,
):
    return service.get_mapping_suggestions(upload_job_id=upload_job_id, user=user)


@router.post("/api/uploads/{upload_job_id}/validate", response_model=ValidateUploadResponse)
def validate_upload(upload_job_id: str, user: CurrentUser, service: UploadServiceDep):
    return service.validate_upload(upload_job_id=upload_job_id, user=user)


@router.post("/api/uploads/{upload_job_id}/confirm", response_model=ConfirmUploadResponse)
def confirm_upload(upload_job_id: str, user: CurrentUser, service: UploadServiceDep):
    return service.confirm_upload(upload_job_id=upload_job_id, user=user)


@router.get("/api/uploads/{upload_job_id}/errors", response_model=UploadErrorsResponse)
def get_upload_errors(upload_job_id: str, user: CurrentUser, service: UploadServiceDep):
    return service.get_errors(upload_job_id=upload_job_id, user=user)

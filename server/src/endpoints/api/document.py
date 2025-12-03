from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from database.models.user_model import UserModel
from database.repositories import DocumentRepository
from endpoints.dependencies import get_db, get_current_user
from endpoints.models.document import DocumentResponse, DocumentUploadResponse
from core.models.document_status import DocumentStatus

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    document_repo = DocumentRepository(db)
    document = document_repo.create(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        status=DocumentStatus.UPLOADED,
        chunk_count=0,
        page_count=0,
        file_size_mb=round(file_size_mb, 2)
    )

    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        status=document.status.value,
        message="Document uploaded successfully. Processing will begin shortly."
    )


@router.get("/", response_model=List[DocumentResponse])
def get_user_documents(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document_repo = DocumentRepository(db)
    documents = document_repo.get_by_user_id(current_user.id)

    return [
        DocumentResponse(
            id=d.id,
            user_id=d.user_id,
            filename=d.filename,
            file_path=d.file_path,
            upload_date=d.upload_date,
            status=d.status.value,
            chunk_count=d.chunk_count,
            page_count=d.page_count,
            file_size_mb=d.file_size_mb
        )
        for d in documents
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document_repo = DocumentRepository(db)
    document = document_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )

    return DocumentResponse(
        id=document.id,
        user_id=document.user_id,
        filename=document.filename,
        file_path=document.file_path,
        upload_date=document.upload_date,
        status=document.status.value,
        chunk_count=document.chunk_count,
        page_count=document.page_count,
        file_size_mb=document.file_size_mb
    )
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.models.user_model import UserModel
from database.repositories import QueryRepository, DocumentRepository, UserRepository, TransactionRepository
from endpoints.dependencies import get_db, get_current_user
from endpoints.models.query import QueryRequest, QueryResponse
from core.models.query_status import QueryStatus
from core.models.document_status import DocumentStatus
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus
from core.query import Query
from core.user import User
from core.document import Document

router = APIRouter(prefix="/queries", tags=["Queries"])


@router.post("/", response_model=QueryResponse, status_code=status.HTTP_201_CREATED)
async def create_query(
    request: QueryRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document_repo = DocumentRepository(db)
    query_repo = QueryRepository(db)
    user_repo = UserRepository(db)
    transaction_repo = TransactionRepository(db)

    document_model = document_repo.get_by_id(request.document_id)

    if not document_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document_model.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to query this document"
        )

    if document_model.status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready for queries. Current status: {document_model.status.value}"
        )

    query_model = query_repo.create(
        user_id=current_user.id,
        document_id=request.document_id,
        question=request.question,
        status=QueryStatus.PENDING
    )

    user = User(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        password_hash=current_user.password_hash,
        balance=current_user.balance,
        role=current_user.role,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )

    document = Document(
        id=document_model.id,
        user_id=document_model.user_id,
        filename=document_model.filename,
        file_path=document_model.file_path,
        upload_date=document_model.upload_date,
        status=document_model.status,
        chunk_count=document_model.chunk_count,
        page_count=document_model.page_count,
        file_size_mb=document_model.file_size_mb
    )

    query = Query(
        id=query_model.id,
        user_id=current_user.id,
        document_id=request.document_id,
        question=request.question
    )

    if not user.is_admin() and current_user.balance < 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Current balance: {current_user.balance:.2f}. Please top up your account."
        )

    try:
        answer = await query.execute(
            user=user,
            document=document,
            llm_service=None,
            qdrant_service=None,
            reranker_service=None
        )

        query_model.answer = answer
        query_model.status = QueryStatus.COMPLETED
        query_model.cost = query.cost
        query_model.input_tokens = query.input_tokens
        query_model.output_tokens = query.output_tokens
        query_model.total_tokens = query.total_tokens
        query_repo.update(query_model)

        user_repo.update_balance(current_user.id, current_user.balance - query.cost)

        if query.cost > 0:
            transaction_repo.create(
                user_id=current_user.id,
                amount=query.cost,
                transaction_type=TransactionType.QUERY_CHARGE,
                status=TransactionStatus.COMPLETED,
                description=f"Query #{query_model.id}: {request.question[:50]}...",
                related_query_id=query_model.id
            )

    except Exception as e:
        query_model.status = QueryStatus.FAILED
        query_model.answer = f"Error: {str(e)}"
        query_repo.update(query_model)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return QueryResponse(
        id=query_model.id,
        user_id=query_model.user_id,
        document_id=query_model.document_id,
        question=query_model.question,
        answer=query_model.answer,
        cost=query_model.cost,
        input_tokens=query_model.input_tokens,
        output_tokens=query_model.output_tokens,
        total_tokens=query_model.total_tokens,
        timestamp=query_model.timestamp,
        status=query_model.status.value
    )


@router.get("/history", response_model=List[QueryResponse])
def get_query_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query_repo = QueryRepository(db)
    queries = query_repo.get_by_user_id(current_user.id)

    return [
        QueryResponse(
            id=q.id,
            user_id=q.user_id,
            document_id=q.document_id,
            question=q.question,
            answer=q.answer,
            cost=q.cost,
            input_tokens=q.input_tokens,
            output_tokens=q.output_tokens,
            total_tokens=q.total_tokens,
            timestamp=q.timestamp,
            status=q.status.value
        )
        for q in queries
    ]


@router.get("/{query_id}", response_model=QueryResponse)
def get_query(
    query_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query_repo = QueryRepository(db)
    query = query_repo.get_by_id(query_id)

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )

    if query.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this query"
        )

    return QueryResponse(
        id=query.id,
        user_id=query.user_id,
        document_id=query.document_id,
        question=query.question,
        answer=query.answer,
        cost=query.cost,
        input_tokens=query.input_tokens,
        output_tokens=query.output_tokens,
        total_tokens=query.total_tokens,
        timestamp=query.timestamp,
        status=query.status.value
    )
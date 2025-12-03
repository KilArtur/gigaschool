from fastapi import APIRouter
from endpoints.api.auth import router as auth_router
from endpoints.api.document import router as document_router
from endpoints.api.query import router as query_router
from endpoints.api.transaction import router as transaction_router
from endpoints.api.user import router as user_router


main_router = APIRouter()

main_router.include_router(auth_router)
main_router.include_router(document_router)
main_router.include_router(query_router)
main_router.include_router(transaction_router)
main_router.include_router(user_router)


import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.engine import SessionLocal
from database.repositories import UserRepository, WalletRepository, TransactionRepository
from core.models.user_role import UserRole
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus
from datetime import datetime


def seed_demo_data():
    session = SessionLocal()

    try:
        user_repo = UserRepository(session)
        wallet_repo = WalletRepository(session)
        transaction_repo = TransactionRepository(session)

        print("Seeding demo data...")

        existing_admin = user_repo.get_by_username("admin")
        if existing_admin:
            print("Admin user already exists, skipping...")
        else:
            admin_user = user_repo.create(
                username="admin",
                email="admin@gigaschool.com",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW6V3z8QJ5K6",
                balance=0.0,
                role=UserRole.ADMIN,
                is_active=True
            )
            print(f"Created admin user: {admin_user.username} (ID: {admin_user.id})")

            admin_wallet = wallet_repo.create(
                user_id=admin_user.id,
                balance=0.0
            )
            print(f"Created wallet for admin (ID: {admin_wallet.id})")

        existing_demo = user_repo.get_by_username("demo_user")
        if existing_demo:
            print("Demo user already exists, skipping...")
        else:
            demo_user = user_repo.create(
                username="demo_user",
                email="demo@gigaschool.com",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW6V3z8QJ5K6",
                balance=1000.0,
                role=UserRole.REGULAR,
                is_active=True
            )
            print(f"Created demo user: {demo_user.username} (ID: {demo_user.id})")

            demo_wallet = wallet_repo.create(
                user_id=demo_user.id,
                balance=1000.0
            )
            print(f"Created wallet for demo user (ID: {demo_wallet.id}, Balance: {demo_wallet.balance})")

            demo_transaction = transaction_repo.create(
                user_id=demo_user.id,
                amount=1000.0,
                transaction_type=TransactionType.TOP_UP,
                status=TransactionStatus.COMPLETED,
                timestamp=datetime.now(),
                description="Initial demo balance"
            )
            print(f"Created initial transaction (ID: {demo_transaction.id})")

        print("Demo data seeded successfully!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed_demo_data()
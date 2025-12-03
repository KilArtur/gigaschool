import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.engine import SessionLocal
from database.repositories import UserRepository, WalletRepository, TransactionRepository
from core.models.user_role import UserRole
from core.models.transaction_type import TransactionType
from core.models.transaction_status import TransactionStatus
from datetime import datetime


def test_user_operations():
    print("\n=== Testing User Operations ===")
    session = SessionLocal()
    user_repo = UserRepository(session)

    users = user_repo.get_all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"  - {user.username} ({user.email}) - Role: {user.role.value}, Balance: {user.balance}, Active: {user.is_active}")

    admin = user_repo.get_by_username("admin")
    if admin:
        print(f"\nAdmin user found: {admin.username} (ID: {admin.id})")

    demo = user_repo.get_by_username("demo_user")
    if demo:
        print(f"Demo user found: {demo.username} (ID: {demo.id})")

    session.close()


def test_wallet_operations():
    print("\n=== Testing Wallet Operations ===")
    session = SessionLocal()
    user_repo = UserRepository(session)
    wallet_repo = WalletRepository(session)

    demo = user_repo.get_by_username("demo_user")
    if demo:
        wallet = wallet_repo.get_by_user_id(demo.id)
        if wallet:
            print(f"Demo user wallet: Balance = {wallet.balance}")

            print("\nAdding 500 to balance...")
            wallet_repo.add_balance(wallet.id, 500.0)
            wallet = wallet_repo.get_by_id(wallet.id)
            print(f"New balance: {wallet.balance}")

            print("\nDeducting 200 from balance...")
            wallet_repo.deduct_balance(wallet.id, 200.0)
            wallet = wallet_repo.get_by_id(wallet.id)
            print(f"New balance: {wallet.balance}")

    session.close()


def test_transaction_operations():
    print("\n=== Testing Transaction Operations ===")
    session = SessionLocal()
    user_repo = UserRepository(session)
    transaction_repo = TransactionRepository(session)

    demo = user_repo.get_by_username("demo_user")
    if demo:
        print(f"\nCreating new transaction for {demo.username}...")
        transaction = transaction_repo.create(
            user_id=demo.id,
            amount=100.0,
            transaction_type=TransactionType.TOP_UP,
            status=TransactionStatus.PENDING,
            description="Test top-up"
        )
        print(f"Created transaction ID: {transaction.id}, Status: {transaction.status.value}")

        print("\nMarking transaction as completed...")
        transaction_repo.mark_completed(transaction.id)
        transaction = transaction_repo.get_by_id(transaction.id)
        print(f"Transaction status: {transaction.status.value}")

        print(f"\nAll transactions for {demo.username}:")
        transactions = transaction_repo.get_by_user_id(demo.id)
        for t in transactions:
            print(f"  - ID: {t.id}, Type: {t.transaction_type.value}, Amount: {t.amount}, Status: {t.status.value}")

    session.close()


def test_balance_deduction():
    print("\n=== Testing Balance Deduction for Query ===")
    session = SessionLocal()
    user_repo = UserRepository(session)
    wallet_repo = WalletRepository(session)
    transaction_repo = TransactionRepository(session)

    demo = user_repo.get_by_username("demo_user")
    if demo:
        wallet = wallet_repo.get_by_user_id(demo.id)
        print(f"Current balance: {wallet.balance}")

        query_cost = 50.0
        print(f"\nSimulating query with cost: {query_cost}")

        if wallet.balance >= query_cost:
            wallet_repo.deduct_balance(wallet.id, query_cost)

            transaction = transaction_repo.create(
                user_id=demo.id,
                amount=query_cost,
                transaction_type=TransactionType.QUERY_CHARGE,
                status=TransactionStatus.COMPLETED,
                description="Test query charge"
            )

            wallet = wallet_repo.get_by_id(wallet.id)
            print(f"Balance after deduction: {wallet.balance}")
            print(f"Transaction created: ID {transaction.id}")
        else:
            print("Insufficient balance!")

    session.close()


def test_transaction_history():
    print("\n=== Testing Transaction History ===")
    session = SessionLocal()
    user_repo = UserRepository(session)
    transaction_repo = TransactionRepository(session)

    demo = user_repo.get_by_username("demo_user")
    if demo:
        transactions = transaction_repo.get_by_user_id(demo.id)
        print(f"\nTransaction history for {demo.username} ({len(transactions)} transactions):")
        for t in transactions:
            print(f"  [{t.timestamp}] {t.transaction_type.value}: {t.amount} ({t.status.value}) - {t.description}")

    session.close()


if __name__ == "__main__":
    print("Starting system tests...")

    test_user_operations()
    test_wallet_operations()
    test_transaction_operations()
    test_balance_deduction()
    test_transaction_history()

    print("\n=== All tests completed ===")
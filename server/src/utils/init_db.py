import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import argparse
from database.engine import engine
from database.base import Base
from database.models import UserModel, WalletModel, TransactionModel, DocumentModel, QueryModel


def create_tables():
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def drop_tables():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped successfully!")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument("--drop", action="store_true", help="Drop all tables before creating")
    args = parser.parse_args()

    if args.drop:
        drop_tables()

    create_tables()
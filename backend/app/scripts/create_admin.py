"""
create_admin.py — CLI script to create an admin user.

Usage:
    python -m app.scripts.create_admin --username admin --password s3cr3t
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select

# Ensure the backend package is importable when run directly
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.security.auth import hash_password


async def create_admin(username: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[ERROR] Admin user '{username}' already exists.")
            sys.exit(1)

        admin = AdminUser(
            username=username,
            hashed_password=hash_password(password),
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"[OK] Admin user '{username}' created successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Voxora admin user")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password (min 8 chars)")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("[ERROR] Password must be at least 8 characters.")
        sys.exit(1)

    asyncio.run(create_admin(args.username, args.password))


if __name__ == "__main__":
    main()

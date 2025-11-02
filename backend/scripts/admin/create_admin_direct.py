#!/usr/bin/env python3
"""
Script to create an admin user for the Qdrant CMS.
Run this script to create the first admin user.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.models import User, Document, DocumentChunk, Tag  # Import models to ensure tables are created
from app.services.auth_service import get_password_hash
from config import settings


from database import Base, engine

async def create_admin_user():
    """Create an admin user if one doesn't exist"""
    # Create tables first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create database session
    async with AsyncSession(engine) as session:
        try:
            # Check if any admin user exists
            result = await session.execute(select(User).where(User.is_admin == "true"))
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print(f"Admin user already exists: {existing_admin.username}")
                return

            # Get admin credentials from environment or prompt
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

            if not admin_password or admin_password == "admin123":
                print("WARNING: Using default admin password. Please change it after first login!")
                print(f"Default credentials: {admin_username} / {admin_password}")

            # Check if username or email already exists
            result = await session.execute(
                select(User).where(
                    (User.username == admin_username) | (User.email == admin_email)
                )
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"User with username '{admin_username}' or email '{admin_email}' already exists.")
                return

            # Create admin user
            hashed_password = get_password_hash(admin_password)
            admin_user = User(
                username=admin_username,
                email=admin_email,
                hashed_password=hashed_password,
                is_admin="true"
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print(f"Admin user created successfully!")
            print(f"Username: {admin_user.username}")
            print(f"Email: {admin_user.email}")
            print(f"Is Admin: {admin_user.is_admin}")

        except Exception as e:
            print(f"Error creating admin user: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    print("Creating admin user...")
    asyncio.run(create_admin_user())
    print("Done!")
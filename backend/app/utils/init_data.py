import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User
from app.services.auth_service import get_password_hash
from database import async_session_maker

async def ensure_default_admin():
    """
    Ensure that a default admin user exists in the database.
    This is called on application startup.
    """
    async with async_session_maker() as session:
        try:
            # Check if admin user exists
            result = await session.execute(select(User).where(User.username == "admin"))
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print(f"Admin user 'admin' already exists.")
                return

            print("Creating default admin user...")
            
            # Default credentials
            admin_username = "admin"
            admin_email = "admin@example.com"
            admin_password = "admin123"
            
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
            print(f"Default admin user created successfully: {admin_username} / {admin_password}")

        except Exception as e:
            print(f"Error ensuring default admin user: {e}")
            await session.rollback()

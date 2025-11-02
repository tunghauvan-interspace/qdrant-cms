#!/usr/bin/env python3
"""
Create admin user for Qdrant CMS
"""
import requests
import os
from typing import Optional

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Admin credentials from environment or defaults
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def create_admin_user():
    """Create admin user via API"""
    url = f"{BASE_URL}/api/auth/register"

    payload = {
        "username": ADMIN_USERNAME,
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "is_admin": "true"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        print("✅ Admin user created successfully!")
        print(f"   Username: {ADMIN_USERNAME}")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print("\n⚠️  IMPORTANT: Change the default password after first login!")

    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            print("ℹ️  Admin user already exists")
        else:
            print(f"❌ Failed to create admin user: {e}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_admin_user()
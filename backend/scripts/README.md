# Backend Scripts

This directory contains utility scripts for managing and maintaining the Qdrant CMS backend.

## Directory Structure

```
scripts/
├── admin/           # Admin user management scripts
├── database/        # Database management and migration scripts
└── qdrant/          # Qdrant vector database management scripts
```

## Admin Scripts (`admin/`)

### `create_admin_api.py`
Creates an admin user via the REST API. Requires the backend service to be running.

**Usage:**
```bash
cd backend
python scripts/admin/create_admin_api.py
```

**Environment Variables:**
- `ADMIN_USERNAME`: Admin username (default: "admin")
- `ADMIN_EMAIL`: Admin email (default: "admin@example.com")
- `ADMIN_PASSWORD`: Admin password (default: "admin123")
- `BASE_URL`: Backend API URL (default: "http://localhost:8000")

### `create_admin_direct.py`
Creates an admin user directly in the database. Useful for initial setup or when the API is not available.

**Usage:**
```bash
cd backend
python scripts/admin/create_admin_direct.py
```

**Environment Variables:** Same as `create_admin_api.py`

## Database Scripts (`database/`)

### `migrate_database.py`
Database migration script that adds new tables and columns for advanced features like versioning, sharing, analytics, and favorites.

**Usage:**
```bash
cd backend
python scripts/database/migrate_database.py
```

**Features:**
- Adds `last_modified` and `version` columns to documents table
- Creates tables for document versions, shares, analytics, and favorites
- Safe to run multiple times (idempotent)

### `check_docs.py`
Inspects the database and lists all documents with their IDs and filenames.

**Usage:**
```bash
cd backend
python scripts/database/check_docs.py
```

## Qdrant Scripts (`qdrant/`)

### `recreate_collection.py`
Recreates the 'documents' collection in Qdrant. Useful for resetting the vector database.

**Usage:**
```bash
cd backend
python scripts/qdrant/recreate_collection.py
```

**Note:** This will delete all existing vectors in the 'documents' collection. Use with caution.

### `recreate_memory.py`
Recreates the 'memory' collection in Qdrant. Useful for resetting the memory vector database.

**Usage:**
```bash
cd backend
python scripts/qdrant/recreate_memory.py
```

**Note:** This will delete all existing vectors in the 'memory' collection. Use with caution.

## Docker Usage

When using Docker, run scripts from within the backend container:

```bash
# Create admin user via API
docker compose exec backend python scripts/admin/create_admin_api.py

# Run database migration
docker compose exec backend python scripts/database/migrate_database.py

# Check documents
docker compose exec backend python scripts/database/check_docs.py

# Recreate Qdrant collections
docker compose exec backend python scripts/qdrant/recreate_collection.py
docker compose exec backend python scripts/qdrant/recreate_memory.py
```
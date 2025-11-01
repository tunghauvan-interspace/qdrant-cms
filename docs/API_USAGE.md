# API Usage Guide - Advanced Features

This guide demonstrates how to use the new advanced features of the Qdrant CMS API.

## Table of Contents
- [Document Editing & Versioning](#document-editing--versioning)
- [Document Sharing & Permissions](#document-sharing--permissions)
- [Analytics & Tracking](#analytics--tracking)
- [Favorites](#favorites)
- [Bulk Operations](#bulk-operations)
- [Export Features](#export-features)

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:

```bash
Authorization: Bearer <your_token>
```

## Document Editing & Versioning

### Update Document Metadata

Update a document's description, tags, or visibility:

```bash
curl -X PUT http://localhost:8000/api/documents/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "tags": ["tag1", "tag2"],
    "is_public": "public"
  }'
```

**Response:**
```json
{
  "id": 1,
  "original_filename": "document.pdf",
  "description": "Updated description",
  "tags": [{"id": 1, "name": "tag1"}, {"id": 2, "name": "tag2"}],
  "is_public": "public",
  "version": 2,
  "last_modified": "2024-11-01T12:00:00"
}
```

### Get Version History

```bash
curl -X GET http://localhost:8000/api/documents/1/versions \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
[
  {
    "id": 2,
    "version_number": 2,
    "description": "Updated description",
    "tags_snapshot": ["tag1", "tag2"],
    "is_public_snapshot": "public",
    "created_at": "2024-11-01T12:00:00",
    "created_by_id": 1,
    "change_summary": "Description updated; Tags updated; Visibility changed to public"
  },
  {
    "id": 1,
    "version_number": 1,
    "description": "Original description",
    "tags_snapshot": ["old-tag"],
    "is_public_snapshot": "private",
    "created_at": "2024-11-01T10:00:00",
    "created_by_id": 1,
    "change_summary": "Initial version"
  }
]
```

### Rollback to Previous Version

```bash
curl -X POST http://localhost:8000/api/documents/1/versions/1/rollback \
  -H "Authorization: Bearer <token>"
```

This will restore the document to version 1, creating a new version snapshot.

## Document Sharing & Permissions

### Share a Document

Grant a user access to your document with specific permissions:

```bash
curl -X POST http://localhost:8000/api/documents/1/share \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "permission": "edit"
  }'
```

**Permissions:**
- `view`: Can only view and download
- `edit`: Can modify metadata and content
- `admin`: Full control including sharing management

**Response:**
```json
{
  "id": 1,
  "document_id": 1,
  "user_id": 5,
  "permission": "edit",
  "shared_at": "2024-11-01T12:00:00",
  "shared_by_id": 1,
  "user": {
    "id": 5,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### List Document Shares

```bash
curl -X GET http://localhost:8000/api/documents/1/shares \
  -H "Authorization: Bearer <token>"
```

### Remove a Share

```bash
curl -X DELETE http://localhost:8000/api/documents/shares/1 \
  -H "Authorization: Bearer <token>"
```

### Get Documents Shared With Me

```bash
curl -X GET http://localhost:8000/api/documents/shared-with-me \
  -H "Authorization: Bearer <token>"
```

## Analytics & Tracking

### Track Document View

Automatically track when a user views a document:

```bash
curl -X POST http://localhost:8000/api/documents/1/analytics/view \
  -H "Authorization: Bearer <token>"
```

### Track Document Download

```bash
curl -X POST http://localhost:8000/api/documents/1/analytics/download \
  -H "Authorization: Bearer <token>"
```

### Get Document Analytics

```bash
curl -X GET "http://localhost:8000/api/documents/1/analytics?days=30" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "document_id": 1,
  "total_views": 150,
  "total_downloads": 45,
  "total_search_hits": 23,
  "unique_viewers": 12,
  "recent_views": [
    {
      "id": 100,
      "action": "view",
      "timestamp": "2024-11-01T12:00:00",
      "user_id": 5
    }
  ],
  "period_days": 30
}
```

### Get Popular Documents

```bash
curl -X GET "http://localhost:8000/api/documents/analytics/popular?limit=10&days=30" \
  -H "Authorization: Bearer <token>"
```

## Favorites

### Add to Favorites

```bash
curl -X POST http://localhost:8000/api/documents/1/favorite \
  -H "Authorization: Bearer <token>"
```

### Remove from Favorites

```bash
curl -X DELETE http://localhost:8000/api/documents/1/favorite \
  -H "Authorization: Bearer <token>"
```

### Get Favorite Documents

```bash
curl -X GET http://localhost:8000/api/documents/favorites \
  -H "Authorization: Bearer <token>"
```

## Bulk Operations

### Bulk Update Documents

Update multiple documents at once:

```bash
curl -X POST http://localhost:8000/api/documents/bulk/update \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2, 3],
    "updates": {
      "description": "Quarterly Report",
      "tags": ["report", "2024"],
      "is_public": "private"
    }
  }'
```

**Response:**
```json
{
  "updated_count": 3,
  "errors": []
}
```

### Bulk Share Documents

Share multiple documents with a user:

```bash
curl -X POST http://localhost:8000/api/documents/bulk/share \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2, 3],
    "user_id": 5,
    "permission": "view"
  }'
```

## Export Features

### Export as JSON

```bash
curl -X POST http://localhost:8000/api/documents/export/json \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2, 3]
  }'
```

**Response:**
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "document.pdf",
      "description": "My document",
      "tags": ["tag1", "tag2"],
      "version": 2
    }
  ],
  "count": 1
}
```

### Export as ZIP

Download documents as a ZIP archive:

```bash
curl -X POST http://localhost:8000/api/documents/export/zip \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2, 3]
  }' \
  --output documents.zip
```

This will download a ZIP file containing:
- All selected documents in their original format
- A `metadata.json` file with document information

### Export as CSV

Export document metadata to CSV:

```bash
curl -X POST http://localhost:8000/api/documents/export/csv \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2, 3]
  }' \
  --output documents.csv
```

## Permission System

The permission system works hierarchically:

1. **Owner**: Full access to all operations
2. **Admin share**: Can manage shares, edit, and view
3. **Edit share**: Can edit metadata and view
4. **View share**: Can only view and download
5. **Public documents**: Anyone can view

### Permission Checks

All endpoints automatically check permissions:

- **View permission required**: preview, download, get analytics
- **Edit permission required**: update metadata, add to versions
- **Admin permission required**: share management, delete

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid data)
- `401`: Unauthorized (invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `500`: Server error

**Error Response Format:**
```json
{
  "detail": "You don't have permission to edit this document"
}
```

## Rate Limiting

Currently, there are no rate limits, but they may be added in production. It's recommended to:
- Cache document data when possible
- Batch operations using bulk endpoints
- Track analytics asynchronously

## Best Practices

1. **Versioning**: Always provide meaningful change summaries when updating documents
2. **Permissions**: Use the minimum required permission level for shares
3. **Analytics**: Track views and downloads to understand document usage
4. **Bulk Operations**: Use bulk endpoints when operating on multiple documents
5. **Export**: Regularly export important documents for backup

## Example: Complete Workflow

Here's a complete workflow demonstrating multiple features:

```bash
# 1. Upload a document
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@report.pdf" \
  -F "description=Q3 Report" \
  -F "tags=report,q3,2024" \
  -F "is_public=private"

# Document ID: 1

# 2. Share with team members
curl -X POST http://localhost:8000/api/documents/1/share \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 5, "permission": "edit"}'

# 3. Track when someone views it
curl -X POST http://localhost:8000/api/documents/1/analytics/view \
  -H "Authorization: Bearer <token>"

# 4. Update the document
curl -X PUT http://localhost:8000/api/documents/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"description": "Q3 Report - Final Version"}'

# 5. Check analytics
curl -X GET http://localhost:8000/api/documents/1/analytics \
  -H "Authorization: Bearer <token>"

# 6. Export for backup
curl -X POST http://localhost:8000/api/documents/export/zip \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"document_ids": [1]}' \
  --output backup.zip
```

## Support

For more information, see:
- [Main README](../README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [GitHub Issues](https://github.com/tunghauvan-interspace/qdrant-cms/issues)

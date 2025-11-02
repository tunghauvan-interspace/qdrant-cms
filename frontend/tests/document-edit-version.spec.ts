import { test, expect } from '@playwright/test';

test.describe('Document Edit Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          is_admin: 'false'
        })
      });
    });

    // Mock document list
    await page.route('**/api/documents/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            filename: 'test-doc.pdf',
            original_filename: 'test-document.pdf',
            file_type: 'pdf',
            file_size: 2048,
            upload_date: '2024-01-01T00:00:00',
            owner_id: 1,
            description: 'Test document for editing',
            is_public: 'private',
            tags: [
              { id: 1, name: 'test' },
              { id: 2, name: 'demo' }
            ],
            version: 1,
            last_modified: '2024-01-01T00:00:00'
          }
        ])
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display edit button for documents', async ({ page }) => {
    // Wait for document list to load
    await expect(page.getByText('test-document.pdf')).toBeVisible();
    
    // Check for edit button
    const editButton = page.getByRole('button', { name: /edit test-document.pdf/i });
    await expect(editButton).toBeVisible();
  });

  test('should open edit modal when edit button is clicked', async ({ page }) => {
    // Click edit button
    await page.getByRole('button', { name: /edit test-document.pdf/i }).click();
    
    // Check if modal is displayed
    await expect(page.getByRole('heading', { name: 'Edit Document' })).toBeVisible();
    await expect(page.getByText('test-document.pdf')).toBeVisible();
  });

  test('should pre-fill form with document data', async ({ page }) => {
    // Click edit button
    await page.getByRole('button', { name: /edit test-document.pdf/i }).click();
    
    // Check form fields are pre-filled
    await expect(page.locator('#edit-description')).toHaveValue('Test document for editing');
    await expect(page.locator('#edit-tags')).toHaveValue('test, demo');
    await expect(page.locator('#edit-visibility')).toHaveValue('private');
  });

  test('should allow updating document metadata', async ({ page }) => {
    let updateCalled = false;
    
    // Mock update API
    await page.route('**/api/documents/1', async (route) => {
      if (route.request().method() === 'PUT') {
        updateCalled = true;
        const postData = JSON.parse(await route.request().postData() || '{}');
        expect(postData.description).toBe('Updated description');
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            filename: 'test-doc.pdf',
            original_filename: 'test-document.pdf',
            file_type: 'pdf',
            file_size: 2048,
            upload_date: '2024-01-01T00:00:00',
            owner_id: 1,
            description: 'Updated description',
            is_public: 'public',
            tags: [],
            version: 2
          })
        });
      }
    });
    
    // Click edit button
    await page.getByRole('button', { name: /edit test-document.pdf/i }).click();
    
    // Update description
    await page.locator('#edit-description').fill('Updated description');
    
    // Change visibility
    await page.locator('#edit-visibility').selectOption('public');
    
    // Click save
    await page.getByRole('button', { name: /Save Changes/i }).click();
    
    // Wait for modal to close
    await expect(page.getByRole('heading', { name: 'Edit Document' })).not.toBeVisible({ timeout: 5000 });
    
    // Verify update was called
    expect(updateCalled).toBe(true);
  });

  test('should allow replacing document file', async ({ page }) => {
    // Click edit button
    await page.getByRole('button', { name: /edit test-document.pdf/i }).click();
    
    // Check for file upload input
    const fileInput = page.locator('#edit-file');
    await expect(fileInput).toBeVisible();
    
    // Check help text
    await expect(page.getByText(/Upload a new file to replace/i)).toBeVisible();
  });

  test('should close modal when cancel is clicked', async ({ page }) => {
    // Click edit button
    await page.getByRole('button', { name: /edit test-document.pdf/i }).click();
    
    // Verify modal is open
    await expect(page.getByRole('heading', { name: 'Edit Document' })).toBeVisible();
    
    // Click cancel
    await page.getByRole('button', { name: 'Cancel' }).click();
    
    // Verify modal is closed
    await expect(page.getByRole('heading', { name: 'Edit Document' })).not.toBeVisible();
  });

  test('should display success message after update', async ({ page }) => {
    // Mock successful update
    await page.route('**/api/documents/1', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            filename: 'test-doc.pdf',
            original_filename: 'test-document.pdf',
            file_type: 'pdf',
            file_size: 2048,
            upload_date: '2024-01-01T00:00:00',
            owner_id: 1,
            description: 'Updated',
            is_public: 'private',
            tags: [],
            version: 2
          })
        });
      }
    });
    
    // Click edit button
    await page.getByRole('button', { name: /edit test-document.pdf/i }).click();
    
    // Update and save
    await page.locator('#edit-description').fill('Updated');
    await page.getByRole('button', { name: /Save Changes/i }).click();
    
    // Check for success message (toast)
    await expect(page.getByText(/updated successfully/i)).toBeVisible({ timeout: 3000 });
  });
});

test.describe('Version History Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'testuser',
          email: 'test@example.com'
        })
      });
    });

    // Mock document list
    await page.route('**/api/documents/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            filename: 'versioned-doc.pdf',
            original_filename: 'versioned-document.pdf',
            file_type: 'pdf',
            file_size: 3072,
            upload_date: '2024-01-01T00:00:00',
            owner_id: 1,
            description: 'Document with version history',
            is_public: 'private',
            tags: [],
            version: 3
          }
        ])
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display version history button', async ({ page }) => {
    // Wait for document to load
    await expect(page.getByText('versioned-document.pdf')).toBeVisible();
    
    // Check for version history button
    const versionButton = page.getByRole('button', { name: /view versions of versioned-document.pdf/i });
    await expect(versionButton).toBeVisible();
  });

  test('should open version history modal', async ({ page }) => {
    // Mock version history API
    await page.route('**/api/documents/1/versions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 3,
            document_id: 1,
            version_number: 3,
            description: 'Updated document',
            tags_snapshot: ['tag1', 'tag2'],
            is_public_snapshot: 'private',
            created_at: '2024-01-03T00:00:00',
            created_by_id: 1,
            change_summary: 'Updated description and tags'
          },
          {
            id: 2,
            document_id: 1,
            version_number: 2,
            description: 'Second version',
            tags_snapshot: ['tag1'],
            is_public_snapshot: 'private',
            created_at: '2024-01-02T00:00:00',
            created_by_id: 1,
            change_summary: 'Changed visibility'
          },
          {
            id: 1,
            document_id: 1,
            version_number: 1,
            description: 'First version',
            tags_snapshot: [],
            is_public_snapshot: 'private',
            created_at: '2024-01-01T00:00:00',
            created_by_id: 1,
            change_summary: 'Initial version'
          }
        ])
      });
    });
    
    // Click version history button
    await page.getByRole('button', { name: /view versions of versioned-document.pdf/i }).click();
    
    // Check if modal is displayed
    await expect(page.getByRole('heading', { name: 'Version History' })).toBeVisible();
    await expect(page.getByText('versioned-document.pdf')).toBeVisible();
  });

  test('should display version list in modal', async ({ page }) => {
    // Mock version history API
    await page.route('**/api/documents/1/versions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 2,
            document_id: 1,
            version_number: 2,
            description: 'Second version',
            tags_snapshot: ['test'],
            is_public_snapshot: 'private',
            created_at: '2024-01-02T00:00:00',
            created_by_id: 1,
            change_summary: 'Updated tags'
          },
          {
            id: 1,
            document_id: 1,
            version_number: 1,
            description: 'First version',
            tags_snapshot: [],
            is_public_snapshot: 'private',
            created_at: '2024-01-01T00:00:00',
            created_by_id: 1,
            change_summary: 'Initial version'
          }
        ])
      });
    });
    
    // Open version history
    await page.getByRole('button', { name: /view versions of versioned-document.pdf/i }).click();
    
    // Wait for versions to load
    await expect(page.getByText('Version 2')).toBeVisible();
    await expect(page.getByText('Version 1')).toBeVisible();
    
    // Check change summaries
    await expect(page.getByText('Updated tags')).toBeVisible();
    await expect(page.getByText('Initial version')).toBeVisible();
  });

  test('should display rollback button for each version', async ({ page }) => {
    // Mock version history API
    await page.route('**/api/documents/1/versions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            document_id: 1,
            version_number: 1,
            description: 'First version',
            tags_snapshot: [],
            is_public_snapshot: 'private',
            created_at: '2024-01-01T00:00:00',
            created_by_id: 1,
            change_summary: 'Initial version'
          }
        ])
      });
    });
    
    // Open version history
    await page.getByRole('button', { name: /view versions of versioned-document.pdf/i }).click();
    
    // Check for rollback button
    await expect(page.getByRole('button', { name: /Rollback/i }).first()).toBeVisible();
  });

  test('should show loading state while fetching versions', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/documents/1/versions', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });
    
    // Open version history
    await page.getByRole('button', { name: /view versions of versioned-document.pdf/i }).click();
    
    // Check for loading spinner
    const spinner = page.locator('.animate-spin');
    await expect(spinner).toBeVisible();
  });

  test('should display empty state when no versions exist', async ({ page }) => {
    // Mock empty versions
    await page.route('**/api/documents/1/versions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });
    
    // Open version history
    await page.getByRole('button', { name: /view versions of versioned-document.pdf/i }).click();
    
    // Check for empty state message
    await expect(page.getByText('No version history available')).toBeVisible();
  });

  test('should close modal when close button is clicked', async ({ page }) => {
    // Mock version history API
    await page.route('**/api/documents/1/versions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });
    
    // Open version history
    await page.getByRole('button', { name: /view versions of versioned-document.pdf/i }).click();
    
    // Verify modal is open
    await expect(page.getByRole('heading', { name: 'Version History' })).toBeVisible();
    
    // Click close
    await page.getByRole('button', { name: 'Close' }).click();
    
    // Verify modal is closed
    await expect(page.getByRole('heading', { name: 'Version History' })).not.toBeVisible();
  });

  test('should handle rollback action', async ({ page }) => {
    let rollbackCalled = false;
    
    // Mock version history API
    await page.route('**/api/documents/1/versions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            document_id: 1,
            version_number: 1,
            description: 'First version',
            tags_snapshot: [],
            is_public_snapshot: 'private',
            created_at: '2024-01-01T00:00:00',
            created_by_id: 1,
            change_summary: 'Initial version'
          }
        ])
      });
    });
    
    // Mock rollback API
    await page.route('**/api/documents/1/versions/1/rollback', async (route) => {
      if (route.request().method() === 'POST') {
        rollbackCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            filename: 'versioned-doc.pdf',
            original_filename: 'versioned-document.pdf',
            file_type: 'pdf',
            file_size: 3072,
            upload_date: '2024-01-01T00:00:00',
            owner_id: 1,
            description: 'First version',
            is_public: 'private',
            tags: [],
            version: 4
          })
        });
      }
    });
    
    // Open version history
    await page.getByRole('button', { name: /view versions of versioned-document.pdf/i }).click();
    
    // Handle confirmation dialog
    page.on('dialog', dialog => dialog.accept());
    
    // Click rollback button
    await page.getByRole('button', { name: /Rollback/i }).first().click();
    
    // Wait a bit for API call
    await page.waitForTimeout(500);
    
    // Verify rollback was called
    expect(rollbackCalled).toBe(true);
  });
});

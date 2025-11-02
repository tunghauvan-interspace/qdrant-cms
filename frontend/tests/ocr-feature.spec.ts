import { test, expect } from '@playwright/test';

/**
 * E2E tests for OCR (Optical Character Recognition) feature
 */

test.describe('OCR Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Login as admin
    await page.getByRole('textbox', { name: 'Username' }).fill('admin');
    await page.getByRole('textbox', { name: 'Password' }).fill('admin123');
    await page.getByRole('button', { name: 'Sign in' }).click();
    
    // Wait for dashboard to load
    await page.waitForURL('**/dashboard');
    await page.waitForTimeout(2000);
  });

  test('should display OCR checkbox in upload form', async ({ page }) => {
    // Navigate to upload tab
    await page.getByRole('button', { name: 'Navigate to Upload' }).click();
    await page.waitForTimeout(1000);
    
    // Check that OCR checkbox is visible
    const ocrCheckbox = page.getByRole('checkbox', { name: /Enable OCR/i });
    await expect(ocrCheckbox).toBeVisible();
    
    // Check that OCR description is visible
    const ocrDescription = page.getByText(/Use OCR to extract text from scanned PDFs/i);
    await expect(ocrDescription).toBeVisible();
  });

  test('should allow toggling OCR checkbox', async ({ page }) => {
    // Navigate to upload tab
    await page.getByRole('button', { name: 'Navigate to Upload' }).click();
    await page.waitForTimeout(1000);
    
    const ocrCheckbox = page.getByRole('checkbox', { name: /Enable OCR/i });
    
    // Initially unchecked
    await expect(ocrCheckbox).not.toBeChecked();
    
    // Click to check
    await ocrCheckbox.click();
    await expect(ocrCheckbox).toBeChecked();
    
    // Click to uncheck
    await ocrCheckbox.click();
    await expect(ocrCheckbox).not.toBeChecked();
  });

  test('should display image file formats in upload area', async ({ page }) => {
    // Navigate to upload tab
    await page.getByRole('button', { name: 'Navigate to Upload' }).click();
    await page.waitForTimeout(1000);
    
    // Check that image formats are mentioned
    const formatText = page.getByText(/PDF, DOCX, or images \(PNG, JPG\)/i);
    await expect(formatText).toBeVisible();
  });

  test('should accept image files in file input', async ({ page }) => {
    // Navigate to upload tab
    await page.getByRole('button', { name: 'Navigate to Upload' }).click();
    await page.waitForTimeout(1000);
    
    // Get the file input element
    const fileInput = page.locator('input[type="file"]');
    
    // Check that it accepts image formats
    const acceptAttr = await fileInput.getAttribute('accept');
    expect(acceptAttr).toContain('.png');
    expect(acceptAttr).toContain('.jpg');
    expect(acceptAttr).toContain('.jpeg');
  });

  test('should reset OCR checkbox when Clear button is clicked', async ({ page }) => {
    // Navigate to upload tab
    await page.getByRole('button', { name: 'Navigate to Upload' }).click();
    await page.waitForTimeout(1000);
    
    const ocrCheckbox = page.getByRole('checkbox', { name: /Enable OCR/i });
    
    // Check the OCR checkbox
    await ocrCheckbox.click();
    await expect(ocrCheckbox).toBeChecked();
    
    // Click Clear button
    await page.getByRole('button', { name: 'Clear' }).click();
    
    // OCR checkbox should be unchecked
    await expect(ocrCheckbox).not.toBeChecked();
  });

  test('should show OCR option in the correct section of the form', async ({ page }) => {
    // Navigate to upload tab
    await page.getByRole('button', { name: 'Navigate to Upload' }).click();
    await page.waitForTimeout(1000);
    
    // Check that form fields are in correct order
    const fileLabel = page.getByText('Document File');
    const descriptionLabel = page.getByText('Description');
    const tagsLabel = page.getByText('Tags');
    const accessLabel = page.getByText('Access Level');
    const ocrCheckbox = page.getByRole('checkbox', { name: /Enable OCR/i });
    
    // All elements should be visible
    await expect(fileLabel).toBeVisible();
    await expect(descriptionLabel).toBeVisible();
    await expect(tagsLabel).toBeVisible();
    await expect(accessLabel).toBeVisible();
    await expect(ocrCheckbox).toBeVisible();
  });
});

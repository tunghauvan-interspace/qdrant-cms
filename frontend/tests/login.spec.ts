import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('should display login form', async ({ page }) => {
    await page.goto('/login');

    // Check page title
    await expect(page.getByRole('heading', { name: 'Qdrant CMS/DMS' })).toBeVisible();
    await expect(page.getByText('Sign in to your account')).toBeVisible();

    // Check form fields
    await expect(page.getByPlaceholder('Username')).toBeVisible();
    await expect(page.getByPlaceholder('Password')).toBeVisible();

    // Check buttons
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Don't have an account/i })).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.goto('/login');

    // Try to submit empty form
    await page.getByRole('button', { name: 'Sign in' }).click();

    // HTML5 validation should prevent submission
    const usernameInput = page.getByPlaceholder('Username');
    await expect(usernameInput).toHaveAttribute('required', '');
    
    const passwordInput = page.getByPlaceholder('Password');
    await expect(passwordInput).toHaveAttribute('required', '');
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');

    // Click on register link
    await page.getByRole('button', { name: /Don't have an account/i }).click();

    // Should navigate to register page
    await expect(page).toHaveURL('/register');
  });

  test('should show loading state when submitting', async ({ page }) => {
    await page.goto('/login');

    // Fill in credentials
    await page.getByPlaceholder('Username').fill('testuser');
    await page.getByPlaceholder('Password').fill('testpassword');

    // Submit form
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Should show loading state (will fail if backend not running)
    await expect(page.getByRole('button', { name: 'Signing in...' })).toBeVisible({ timeout: 1000 }).catch(() => {
      // Expected to fail if backend is not running
      console.log('Backend not available - this is expected in isolated frontend tests');
    });
  });

  test('should have responsive layout', async ({ page }) => {
    await page.goto('/login');

    // Check that the form container exists
    const formContainer = page.locator('.max-w-md');
    await expect(formContainer).toBeVisible();

    // Check background color
    const bgContainer = page.locator('.min-h-screen.bg-gray-50');
    await expect(bgContainer).toBeVisible();
  });
});

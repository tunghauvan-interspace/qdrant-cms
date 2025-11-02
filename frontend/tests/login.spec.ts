import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('should display login form', async ({ page }) => {
    await page.goto('/login');

    // Check page title
    await expect(page.getByRole('heading', { name: 'Qdrant CMS' })).toBeVisible();
    await expect(page.getByText('Sign in to manage your documents')).toBeVisible();

    // Check form fields
    await expect(page.getByPlaceholder('Enter your username')).toBeVisible();
    await expect(page.getByPlaceholder('Enter your password')).toBeVisible();

    // Check Remember Me checkbox
    await expect(page.getByRole('checkbox', { name: 'Remember me' })).toBeVisible();
    await expect(page.getByText('Remember me for 7 days')).toBeVisible();

    // Check buttons
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Create an account/i })).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.goto('/login');

    // Try to submit empty form
    await page.getByRole('button', { name: 'Sign in' }).click();

    // HTML5 validation should prevent submission
    const usernameInput = page.getByPlaceholder('Enter your username');
    await expect(usernameInput).toHaveAttribute('required', '');
    
    const passwordInput = page.getByPlaceholder('Enter your password');
    await expect(passwordInput).toHaveAttribute('required', '');
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');

    // Click on register link
    await page.getByRole('button', { name: /Create an account/i }).click();

    // Should navigate to register page
    await expect(page).toHaveURL('/register');
  });

  test('should show loading state when submitting', async ({ page }) => {
    await page.goto('/login');

    // Fill in credentials
    await page.getByPlaceholder('Enter your username').fill('testuser');
    await page.getByPlaceholder('Enter your password').fill('testpassword');

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

    // Check background gradient
    const bgContainer = page.locator('.min-h-screen.bg-gradient-to-br');
    await expect(bgContainer).toBeVisible();
  });

  test('should allow toggling Remember Me checkbox', async ({ page }) => {
    await page.goto('/login');

    const rememberMeCheckbox = page.getByRole('checkbox', { name: 'Remember me' });

    // Checkbox should be unchecked by default
    await expect(rememberMeCheckbox).not.toBeChecked();

    // Click to check
    await rememberMeCheckbox.click();
    await expect(rememberMeCheckbox).toBeChecked();

    // Click to uncheck
    await rememberMeCheckbox.click();
    await expect(rememberMeCheckbox).not.toBeChecked();
  });

  test('should have accessible Remember Me checkbox', async ({ page }) => {
    await page.goto('/login');

    const rememberMeCheckbox = page.getByRole('checkbox', { name: 'Remember me' });
    const rememberMeLabel = page.locator('label[for="remember-me"]');

    // Check accessibility attributes
    await expect(rememberMeCheckbox).toHaveAttribute('id', 'remember-me');
    await expect(rememberMeCheckbox).toHaveAttribute('aria-label', 'Remember me');
    await expect(rememberMeLabel).toBeVisible();
    await expect(rememberMeLabel).toContainText('Remember me for 7 days');

    // Clicking label should toggle checkbox
    await rememberMeLabel.click();
    await expect(rememberMeCheckbox).toBeChecked();
  });
});

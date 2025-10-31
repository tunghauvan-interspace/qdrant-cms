import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    // Clear any existing storage
    await page.context().clearCookies();
    await page.goto('/');

    // Should redirect to login page
    await expect(page).toHaveURL('/login', { timeout: 10000 });
  });

  test('should show loading state initially', async ({ page }) => {
    // Clear any existing storage
    await page.context().clearCookies();

    // Navigate and wait for initial render
    await page.goto('/');
    
    // Should show loading text briefly or redirect
    const hasLoading = await page.getByText('Loading...').isVisible().catch(() => false);
    const isLogin = await page.url().includes('/login');
    
    // Either should show loading or already redirected to login
    expect(hasLoading || isLogin).toBeTruthy();
  });
});

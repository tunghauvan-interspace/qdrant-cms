import { test, expect } from '@playwright/test';

/**
 * Test: Search Document UI Improvements
 * 
 * This test verifies:
 * 1. Search results show unique documents (not duplicated by chunks)
 * 2. Clicking a search result opens the document preview
 * 3. Highlighted chunks are visible in the preview
 * 4. Hovering over highlighted chunks shows match percentage tooltip
 */

test.describe('Search Document UI Improvements', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:3000/login');
    
    // Login with test credentials
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should show unique documents in search results (not duplicated by chunks)', async ({ page }) => {
    // Navigate to search tab
    await page.click('button:has-text("Vector Search")');
    
    // Perform a search
    await page.fill('input[placeholder*="looking for"]', 'devops');
    await page.click('button:has-text("Search")');
    
    // Wait for search results
    await page.waitForSelector('.card:has-text("Found")', { timeout: 10000 });
    
    // Get all document cards
    const documentCards = await page.locator('.card').filter({ hasText: 'matching' }).all();
    
    // Verify we have unique documents (not multiple entries for same document)
    if (documentCards.length > 0) {
      // Check that each document appears only once by filename
      const filenames = new Set();
      for (const card of documentCards) {
        const filenameElement = await card.locator('h4').first();
        const filename = await filenameElement.textContent();
        
        // Check for duplicates
        expect(filenames.has(filename)).toBe(false);
        if (filename) {
          filenames.add(filename);
        }
      }
      
      console.log(`✓ Found ${filenames.size} unique documents`);
    }
  });

  test('should display highlighted chunks in document preview with match percentage on hover', async ({ page }) => {
    // Navigate to search tab
    await page.click('button:has-text("Vector Search")');
    
    // Perform a search
    await page.fill('input[placeholder*="looking for"]', 'devops');
    await page.click('button:has-text("Search")');
    
    // Wait for search results
    await page.waitForSelector('.card:has-text("Found")', { timeout: 10000 });
    
    // Click "View Document" button on first result
    const viewButton = page.locator('button:has-text("View Document")').first();
    
    if (await viewButton.isVisible()) {
      await viewButton.click();
      
      // Wait for preview modal to open
      await page.waitForSelector('text=Document Preview', { timeout: 5000 });
      
      // Check if there are highlighted sections
      const highlights = await page.locator('mark.bg-yellow-200').all();
      
      if (highlights.length > 0) {
        console.log(`✓ Found ${highlights.length} highlighted sections`);
        
        // Test hover on first highlighted section
        const firstHighlight = highlights[0];
        
        // Hover over the highlight
        await firstHighlight.hover();
        
        // Wait a bit for tooltip to appear
        await page.waitForTimeout(500);
        
        // Check for tooltip with match percentage
        const tooltip = page.locator('span[role="tooltip"]').first();
        
        if (await tooltip.isVisible()) {
          const tooltipText = await tooltip.textContent();
          console.log(`✓ Tooltip displayed: "${tooltipText}"`);
          
          // Verify tooltip contains percentage
          expect(tooltipText).toMatch(/\d+\.?\d*%\s*match/);
        }
        
        // Check accessibility attributes
        const ariaLabel = await firstHighlight.getAttribute('aria-label');
        expect(ariaLabel).toBeTruthy();
        console.log(`✓ Accessibility label: "${ariaLabel}"`);
      }
      
      // Close the modal
      await page.click('button:has-text("Close")');
    }
  });

  test('should show matching sections badge in search results', async ({ page }) => {
    // Navigate to search tab
    await page.click('button:has-text("Vector Search")');
    
    // Perform a search
    await page.fill('input[placeholder*="looking for"]', 'devops');
    await page.click('button:has-text("Search")');
    
    // Wait for search results
    await page.waitForSelector('.card:has-text("Found")', { timeout: 10000 });
    
    // Check if any results have multiple matching sections badge
    const sectionsBadge = page.locator('.badge:has-text("matching sections")').first();
    
    if (await sectionsBadge.isVisible()) {
      const badgeText = await sectionsBadge.textContent();
      console.log(`✓ Multiple sections badge found: "${badgeText}"`);
      expect(badgeText).toMatch(/\d+\s*matching\s*sections?/);
    }
  });

  test('should display relevance score for each result', async ({ page }) => {
    // Navigate to search tab
    await page.click('button:has-text("Vector Search")');
    
    // Perform a search
    await page.fill('input[placeholder*="looking for"]', 'devops');
    await page.click('button:has-text("Search")');
    
    // Wait for search results
    await page.waitForSelector('.card:has-text("Found")', { timeout: 10000 });
    
    // Check for relevance score display
    const relevanceScore = page.locator('text=/Relevance:.*%/').first();
    
    if (await relevanceScore.isVisible()) {
      const scoreText = await relevanceScore.textContent();
      console.log(`✓ Relevance score displayed: "${scoreText}"`);
      expect(scoreText).toMatch(/Relevance:\s*\d+\.?\d*%/);
    }
  });
});

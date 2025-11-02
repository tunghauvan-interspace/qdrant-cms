import { test, expect, chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.describe('Search UI Screenshot Demo', () => {
  test('demonstrate search highlighting with hover tooltips', async () => {
    // Launch browser
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    
    console.log('Step 1: Navigating to login page...');
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');
    
    console.log('Step 2: Logging in...');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');
    
    console.log('Step 3: Checking for documents...');
    // Check if there are any documents
    const documentsExist = await page.locator('.card:has-text("Total Documents")').isVisible();
    
    if (documentsExist) {
      const docsText = await page.locator('.card:has-text("Total Documents") .text-3xl').textContent();
      console.log(`Found ${docsText} documents`);
      
      // If no documents, upload the sample
      if (docsText === '0') {
        console.log('No documents found. Need to upload a sample document manually.');
        console.log('Please upload /tmp/devops_sample.txt through the UI.');
      }
    }
    
    // Navigate to search
    console.log('Step 4: Navigating to search...');
    await page.click('button:has-text("Vector Search")');
    await page.waitForTimeout(1000);
    
    // Take screenshot of search page
    await page.screenshot({ 
      path: '/tmp/search-01-search-page.png',
      fullPage: false 
    });
    console.log('✓ Screenshot saved: search-01-search-page.png');
    
    // Perform search
    console.log('Step 5: Performing search for "devops"...');
    await page.fill('input[placeholder*="looking for"]', 'devops');
    await page.click('button:has-text("Search")');
    
    // Wait for results
    try {
      await page.waitForSelector('.card:has-text("Found")', { timeout: 10000 });
      
      // Take screenshot of search results
      await page.screenshot({ 
        path: '/tmp/search-02-results.png',
        fullPage: false 
      });
      console.log('✓ Screenshot saved: search-02-results.png');
      
      // Click view document
      console.log('Step 6: Opening document preview...');
      const viewButton = page.locator('button:has-text("View Document")').first();
      if (await viewButton.isVisible()) {
        await viewButton.click();
        await page.waitForSelector('text=Document Preview', { timeout: 5000 });
        await page.waitForTimeout(1000);
        
        // Take screenshot of preview
        await page.screenshot({ 
          path: '/tmp/search-03-preview-modal.png',
          fullPage: false 
        });
        console.log('✓ Screenshot saved: search-03-preview-modal.png');
        
        // Find and hover over first highlight
        console.log('Step 7: Hovering over highlighted section...');
        const highlight = page.locator('mark.bg-yellow-200').first();
        if (await highlight.isVisible()) {
          await highlight.hover();
          await page.waitForTimeout(1000);
          
          // Take screenshot with tooltip
          await page.screenshot({ 
            path: '/tmp/search-04-hover-tooltip.png',
            fullPage: false 
          });
          console.log('✓ Screenshot saved: search-04-hover-tooltip.png');
          
          // Take a closer screenshot of just the modal
          const modal = page.locator('.fixed.inset-0 .bg-white').first();
          await modal.screenshot({ 
            path: '/tmp/search-05-modal-detail.png'
          });
          console.log('✓ Screenshot saved: search-05-modal-detail.png');
        }
      }
    } catch (error) {
      console.log('No search results found or error occurred:', error);
      // Take screenshot of error state
      await page.screenshot({ 
        path: '/tmp/search-error.png',
        fullPage: true 
      });
      console.log('✓ Screenshot saved: search-error.png');
    }
    
    console.log('\nAll screenshots saved to /tmp/');
    console.log('Keeping browser open for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);
    
    await browser.close();
  });
});

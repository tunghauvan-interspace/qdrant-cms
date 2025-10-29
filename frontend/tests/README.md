# Playwright Testing for Qdrant CMS

This directory contains end-to-end tests for the Qdrant CMS frontend using Playwright.

## Setup

### Prerequisites

- Node.js 18+ installed
- Frontend dependencies installed (`npm install` in the `frontend` directory)

### Install Playwright Browsers

After installing the npm dependencies, install the Playwright browsers:

```bash
npx playwright install chromium
```

Or install all browsers:

```bash
npx playwright install
```

To install with system dependencies (Linux):

```bash
npx playwright install --with-deps chromium
```

## Running Tests

### Run all tests

```bash
npm test
```

### Run tests in headed mode (see browser)

```bash
npm run test:headed
```

### Run tests in UI mode (interactive)

```bash
npm run test:ui
```

### Run specific test file

```bash
npx playwright test tests/login.spec.ts
```

### Run tests in a specific browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Reports

After running tests, you can view the HTML report:

```bash
npm run test:report
```

The report will open in your browser showing:
- Test results
- Screenshots of failures
- Traces for debugging

## Test Structure

The tests are organized as follows:

- `tests/login.spec.ts` - Tests for the login page
- `tests/register.spec.ts` - Tests for the registration page
- `tests/home.spec.ts` - Tests for home page redirect behavior

## Running with Backend

For full end-to-end testing including API interactions, ensure the backend services are running:

```bash
# From the root directory
docker compose up -d
```

This will start:
- Qdrant vector database (port 6333)
- Backend API (port 8000)
- Frontend dev server (port 3000)

The tests will automatically start a dev server if one isn't running, as configured in `playwright.config.ts`.

## Test Coverage

Current tests cover:

### Login Page
- Display of login form elements
- Form validation
- Navigation to register page
- Loading states
- Responsive layout

### Register Page
- Display of registration form elements
- Field validation (required fields, email format)
- Navigation to login page
- Loading states
- Proper styling

### Home Page
- Redirect to login when not authenticated
- Loading state display

## Configuration

Tests are configured in `playwright.config.ts`:

- **Base URL**: `http://localhost:3000`
- **Browsers**: Chromium, Firefox, WebKit
- **Parallel execution**: Enabled
- **Retries**: 2 retries on CI, 0 locally
- **Reporter**: HTML reporter
- **Web Server**: Automatically starts dev server before tests

## CI/CD Integration

The tests are CI-ready and can be integrated into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: cd frontend && npm ci

- name: Install Playwright Browsers
  run: cd frontend && npx playwright install --with-deps

- name: Run Playwright tests
  run: cd frontend && npm test

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: frontend/playwright-report/
```

## Debugging Tests

### Debug in UI mode

```bash
npm run test:ui
```

### Run with headed browser and slow motion

```bash
npx playwright test --headed --slow-mo=1000
```

### Run with debug mode

```bash
npx playwright test --debug
```

### View trace

If a test fails, you can view the trace:

```bash
npx playwright show-trace test-results/path-to-trace.zip
```

## Writing New Tests

To add new tests:

1. Create a new `.spec.ts` file in the `tests` directory
2. Import Playwright test utilities:
   ```typescript
   import { test, expect } from '@playwright/test';
   ```
3. Write your tests using the Playwright API
4. Run the tests to verify they work

Example test structure:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/some-page');
    await expect(page.getByRole('heading')).toBeVisible();
  });
});
```

## Troubleshooting

### Browser installation fails

If browser installation fails, try:

```bash
# Clear cache
rm -rf ~/.cache/ms-playwright

# Reinstall
npx playwright install chromium --with-deps
```

### Tests fail to connect to server

Ensure the dev server is running:

```bash
npm run dev
```

Or let Playwright start it automatically (configured in `playwright.config.ts`).

### Port already in use

If port 3000 is already in use, either:
- Stop the conflicting process
- Or configure a different port in `playwright.config.ts`

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Test API](https://playwright.dev/docs/api/class-test)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)

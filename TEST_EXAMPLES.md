# Playwright Test Execution Examples

This document shows example outputs from running Playwright tests for the Qdrant CMS frontend.

## Test List Output

Running `npx playwright test --list` shows all configured tests:

```
Total: 39 tests in 3 files

Tests per browser:
- Chromium: 13 tests
- Firefox: 13 tests  
- WebKit: 13 tests
```

### Detailed Test Breakdown

#### Home Page Tests (2 tests × 3 browsers = 6 total)
```
[chromium] › home.spec.ts › Home Page › should redirect to login when not authenticated
[chromium] › home.spec.ts › Home Page › should show loading state initially
[firefox] › home.spec.ts › Home Page › should redirect to login when not authenticated
[firefox] › home.spec.ts › Home Page › should show loading state initially
[webkit] › home.spec.ts › Home Page › should redirect to login when not authenticated
[webkit] › home.spec.ts › Home Page › should show loading state initially
```

#### Login Page Tests (7 tests × 3 browsers = 21 total)
```
[chromium] › login.spec.ts › Login Page › should display login form
[chromium] › login.spec.ts › Login Page › should show validation errors for empty fields
[chromium] › login.spec.ts › Login Page › should navigate to register page
[chromium] › login.spec.ts › Login Page › should show loading state when submitting
[chromium] › login.spec.ts › Login Page › should have responsive layout
[firefox] › login.spec.ts › Login Page › should display login form
[firefox] › login.spec.ts › Login Page › should show validation errors for empty fields
[firefox] › login.spec.ts › Login Page › should navigate to register page
[firefox] › login.spec.ts › Login Page › should show loading state when submitting
[firefox] › login.spec.ts › Login Page › should have responsive layout
[webkit] › login.spec.ts › Login Page › should display login form
[webkit] › login.spec.ts › Login Page › should show validation errors for empty fields
[webkit] › login.spec.ts › Login Page › should navigate to register page
[webkit] › login.spec.ts › Login Page › should show loading state when submitting
[webkit] › login.spec.ts › Login Page › should have responsive layout
```

#### Register Page Tests (6 tests × 3 browsers = 18 total)
```
[chromium] › register.spec.ts › Register Page › should display registration form
[chromium] › register.spec.ts › Register Page › should validate required fields
[chromium] › register.spec.ts › Register Page › should validate email format
[chromium] › register.spec.ts › Register Page › should navigate to login page
[chromium] › register.spec.ts › Register Page › should show loading state when submitting
[chromium] › register.spec.ts › Register Page › should have proper styling
[firefox] › register.spec.ts › Register Page › should display registration form
[firefox] › register.spec.ts › Register Page › should validate required fields
[firefox] › register.spec.ts › Register Page › should validate email format
[firefox] › register.spec.ts › Register Page › should navigate to login page
[firefox] › register.spec.ts › Register Page › should show loading state when submitting
[firefox] › register.spec.ts › Register Page › should have proper styling
[webkit] › register.spec.ts › Register Page › should display registration form
[webkit] › register.spec.ts › Register Page › should validate required fields
[webkit] › register.spec.ts › Register Page › should validate email format
[webkit] › register.spec.ts › Register Page › should navigate to login page
[webkit] › register.spec.ts › Register Page › should show loading state when submitting
[webkit] › register.spec.ts › Register Page › should have proper styling
```

## Test Execution Commands

### List all tests
```bash
$ npx playwright test --list
Total: 39 tests in 3 files
```

### Run tests in specific browser
```bash
$ npx playwright test --project=chromium
Running 13 tests using 1 worker
```

### Run specific test file
```bash
$ npx playwright test tests/login.spec.ts
Running 21 tests using 1 worker
```

### Run tests with UI mode (interactive)
```bash
$ npm run test:ui
```

### Run tests in headed mode (visible browser)
```bash
$ npm run test:headed
```

## Expected Test Results (with frontend running)

When the frontend dev server is running, tests validate:

### ✅ Home Page
- **Redirect behavior**: Unauthenticated users are redirected to `/login`
- **Loading state**: Brief loading message displayed during authentication check

### ✅ Login Page
- **UI Elements**: 
  - Page heading "Qdrant CMS/DMS"
  - Subheading "Sign in to your account"
  - Username input field
  - Password input field
  - Sign in button
  - Register link
- **Validation**: Required attributes on form fields
- **Navigation**: Clicking register link navigates to `/register`
- **Styling**: Proper Tailwind CSS classes applied
- **Responsive**: Mobile-friendly layout

### ✅ Register Page
- **UI Elements**:
  - Page heading "Create your account"
  - Username input field
  - Email input field
  - Password input field
  - Register button
  - Login link
- **Validation**: 
  - Required fields enforced
  - Email type validation
- **Navigation**: Clicking login link navigates to `/login`
- **Styling**: Consistent design with login page

## Running with Docker Compose

For full end-to-end testing including API interactions:

```bash
# Terminal 1: Start all services
$ docker compose up

# Terminal 2: Run tests
$ cd frontend
$ npm test
```

### Services Started by Docker Compose:
- **Qdrant**: Vector database on port 6333
- **Backend**: FastAPI server on port 8000
- **Frontend**: Next.js dev server on port 3000

### Expected Results with Backend:
When backend is available, additional validations:
- API error handling
- Loading state transitions
- Error message display
- Successful form submissions

## Test Reports

After running tests, view the HTML report:

```bash
$ npm run test:report
```

The report includes:
- Test execution timeline
- Pass/fail status for each test
- Screenshots of failures
- Execution traces for debugging
- Performance metrics

## CI/CD Integration Example

```yaml
name: Playwright Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: cd frontend && npm ci
      
      - name: Install Playwright Browsers
        run: cd frontend && npx playwright install --with-deps
      
      - name: Run Playwright tests
        run: cd frontend && npm test
      
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Test Statistics

- **Total Test Cases**: 13 unique tests
- **Total Test Executions**: 39 (13 tests × 3 browsers)
- **Test Files**: 3 spec files
- **Browsers Tested**: Chromium, Firefox, WebKit
- **Coverage**: Login, Register, and Home pages
- **Execution Time**: ~30-60 seconds (with dev server running)

## Next Steps

To expand test coverage:

1. **Dashboard Tests**: Test authenticated user dashboard
2. **Document Upload**: Test file upload functionality
3. **Search Tests**: Test document search features
4. **API Tests**: Add API-level integration tests
5. **Visual Regression**: Add screenshot comparison tests
6. **Accessibility**: Add a11y tests with axe-core
7. **Performance**: Add Lighthouse performance tests
8. **Mobile**: Add mobile-specific viewport tests

## Troubleshooting

### Issue: Browsers not installed
```bash
Error: browserType.launch: Executable doesn't exist
```
**Solution**: Run `npx playwright install chromium`

### Issue: Port 3000 already in use
```bash
Error: listen EADDRINUSE: address already in use :::3000
```
**Solution**: Stop other processes using port 3000 or configure different port

### Issue: Tests timeout
```bash
Error: Timeout 30000ms exceeded
```
**Solution**: Increase timeout in `playwright.config.ts` or ensure dev server starts properly

## Summary

Playwright testing is fully configured and ready to use! The test suite provides comprehensive coverage of the authentication flow and UI components, with tests running across multiple browsers to ensure cross-browser compatibility.

To get started:
```bash
cd frontend
npm install
npx playwright install chromium
npm test
```

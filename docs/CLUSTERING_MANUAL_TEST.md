# Manual Testing Guide for Clustering Feature

## Prerequisites
1. Docker and Docker Compose installed
2. At least 10-20 documents uploaded to test clustering
3. Documents should have diverse content for better cluster separation

## Test Setup

### 1. Start the Application
```bash
cd qdrant-cms
docker compose up -d --build
```

### 2. Create Admin User (if needed)
```bash
docker compose exec backend python create_admin.py
```

### 3. Upload Test Documents
- Upload at least 10-20 PDF or DOCX files
- Use documents from different topics (e.g., tech, business, health)
- Ensure documents are processed (check backend logs)

## Test Cases

### TC1: Access Clusters Page
**Steps:**
1. Log in to the dashboard
2. Look for "Clusters" navigation item in sidebar
3. Click on "Clusters"

**Expected:**
- Should navigate to `/clusters` page
- Should show clustering configuration panel
- Should show empty state message

**Status:** [ ] Pass [ ] Fail

---

### TC2: Generate Clusters with K-Means
**Steps:**
1. Select "K-Means" algorithm
2. Set "Number of Clusters" to 5
3. Select "UMAP" for visualization
4. Select "Document Level"
5. Click "Generate Clusters"

**Expected:**
- Loading spinner appears
- After processing, scatter plot displays
- 5 different colored clusters visible
- Toast notification shows success message
- Cluster summary cards appear below plot

**Status:** [ ] Pass [ ] Fail

---

### TC3: Hover Over Points
**Steps:**
1. Generate clusters (as in TC2)
2. Hover mouse over different points in scatter plot

**Expected:**
- Tooltip appears showing:
  - Cluster ID
  - Document filename
  - Chunk content (if chunk-level)
- Tooltip follows mouse movement
- No performance lag

**Status:** [ ] Pass [ ] Fail

---

### TC4: Click on Cluster Point
**Steps:**
1. Generate clusters
2. Click on any point in the scatter plot

**Expected:**
- Modal opens showing cluster details
- Modal displays:
  - Cluster ID and size
  - Keywords section with extracted terms
  - Representative documents list
  - Close button (X)

**Status:** [ ] Pass [ ] Fail

---

### TC5: View Cluster Summary Cards
**Steps:**
1. Generate clusters
2. Scroll down to cluster summary cards
3. Click on a summary card

**Expected:**
- Cards show cluster ID and size
- Top 3 keywords displayed per card
- Clicking card opens detail modal
- Cards use distinct border colors

**Status:** [ ] Pass [ ] Fail

---

### TC6: HDBSCAN Clustering
**Steps:**
1. Select "HDBSCAN" algorithm
2. Set "Min Cluster Size" to 5
3. Select "UMAP" for visualization
4. Click "Generate Clusters"

**Expected:**
- Clustering completes successfully
- Variable number of clusters generated (not fixed)
- Some points may be marked as noise (if applicable)
- Clusters have varying sizes

**Status:** [ ] Pass [ ] Fail

---

### TC7: t-SNE Visualization
**Steps:**
1. Select "K-Means" algorithm
2. Set clusters to 3
3. Select "t-SNE" for visualization
4. Click "Generate Clusters"

**Expected:**
- t-SNE processing may take longer
- Scatter plot displays with different point distribution
- Clusters should be more locally grouped
- No errors in console

**Status:** [ ] Pass [ ] Fail

---

### TC8: Chunk-Level Clustering
**Steps:**
1. Select "K-Means" algorithm
2. Set clusters to 5
3. Select "UMAP"
4. Select "Chunk Level"
5. Click "Generate Clusters"

**Expected:**
- More points displayed than document-level
- Hover tooltips show chunk content
- Processing may take longer
- Multiple points from same document may be in different clusters

**Status:** [ ] Pass [ ] Fail

---

### TC9: Responsive Design - Mobile
**Steps:**
1. Open clusters page
2. Resize browser to mobile width (375px)
3. Generate clusters

**Expected:**
- Configuration controls stack vertically
- Scatter plot scales to fit screen
- Controls remain accessible
- Modal overlays properly
- Touch interactions work

**Status:** [ ] Pass [ ] Fail

---

### TC10: Parameter Validation
**Steps:**
1. Try setting Number of Clusters to 1 (should be min 2)
2. Try setting to 25 (should be max 20)
3. Try negative numbers

**Expected:**
- Form validation prevents invalid values
- Input respects min/max constraints
- No crashes or errors

**Status:** [ ] Pass [ ] Fail

---

### TC11: Empty Documents Scenario
**Steps:**
1. Use account with no documents
2. Try to generate clusters

**Expected:**
- Info toast: "No documents available for clustering"
- Cluster result shows empty state
- No errors in console

**Status:** [ ] Pass [ ] Fail

---

### TC12: Keyword Extraction
**Steps:**
1. Generate clusters with documents that have clear topics
2. Open cluster detail modal
3. Review keywords

**Expected:**
- Keywords are relevant to document topics
- 3-5 keywords per cluster
- Stop words filtered out
- Keywords appear in tag-like format

**Status:** [ ] Pass [ ] Fail

---

### TC13: Performance - Large Dataset
**Steps:**
1. Upload 100+ documents
2. Generate document-level clusters with K-Means
3. Time the operation

**Expected:**
- Completes in reasonable time (<30s)
- UI remains responsive
- No memory issues
- Visualization renders smoothly

**Status:** [ ] Pass [ ] Fail

---

### TC14: Color-Blind Friendly Colors
**Steps:**
1. Generate clusters
2. View scatter plot
3. Use color-blind simulator (browser extension)

**Expected:**
- Clusters remain distinguishable
- Colors have good contrast
- Legend is readable
- No color-only information

**Status:** [ ] Pass [ ] Fail

---

### TC15: Accessibility - Keyboard Navigation
**Steps:**
1. Generate clusters
2. Press Tab key repeatedly
3. Navigate to cluster cards
4. Press Enter to open modal
5. Press Esc to close modal

**Expected:**
- Focus indicator visible
- All interactive elements reachable
- Tab order is logical
- Modal can be closed with keyboard
- No keyboard traps

**Status:** [ ] Pass [ ] Fail

---

## Performance Benchmarks

| Test Case | Document Count | Level | Algorithm | Time (seconds) |
|-----------|----------------|-------|-----------|----------------|
| Small     | 10-20         | Doc   | K-Means   |                |
| Medium    | 50-100        | Doc   | K-Means   |                |
| Large     | 100+          | Doc   | K-Means   |                |
| Small     | 10-20         | Chunk | K-Means   |                |
| Medium    | 50-100        | Chunk | K-Means   |                |

## Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Known Issues / Notes

Record any issues found during testing:

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

## Sign-off

Tester: ___________________
Date: ___________________
Version: ___________________

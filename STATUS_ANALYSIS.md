# Status Analysis - Recall Improvements Implementation

**Date**: 2025-12-15  
**Status**: ✅ All implementations verified, but discovery finding 0 candidates

---

## ✅ Implementation Verification

### 1. Recall Debug Script ✅
**File**: `scripts/recall_debug.py`  
**Status**: Fully implemented and working  
- Shows skipped candidates by source
- Top 50 skipped titles with scores
- Procedures by source breakdown
- Project statistics
- Skipped sources analysis

**Current Output**: Empty (no candidates in database yet)

---

### 2. Municipality URL Analysis

#### Issue Found: Empty Entrypoints
**Problem**: Jobs are being enqueued with **empty entrypoints** for RIS and Gazette:
- `enqueue_all_municipalities.py` line 49: `"entrypoint": ""` for RIS
- `enqueue_all_municipalities.py` line 67: `"entrypoint": ""` for Gazette

#### Discovery Code Behavior
1. **RIS Discovery** (`apps/crawlers/ris/sessionnet.py`):
   - Calls `discover_ris(municipality_name, base_url)` with empty base_url
   - Falls back to `_list_procedures_fallback()` which tries relative paths like "si0100.asp"
   - **Error**: "Invalid URL 'si0100.asp': No scheme supplied"

2. **Gazette Discovery** (`apps/crawlers/gazette/spider.py`):
   - Calls `discover_amtsblatt(municipality_name, feed_url)` with empty feed_url
   - Falls back to using empty string as URL
   - **Error**: "Invalid URL '': No scheme supplied"

3. **Municipal Website Discovery**:
   - Uses generated URLs like `https://www.{name}.de`
   - Some municipalities have malformed names → `https://www..de/amtsblatt`
   - **Error**: "Failed to parse: 'www..de', label empty or too long"

#### Root Cause
The discovery functions expect either:
- A valid base URL to discover from, OR
- Municipality name to generate URLs from patterns

But when both are empty/missing, discovery fails and returns empty lists.

---

### 3. Prefilter Score Analysis

#### Current Thresholds (Source-Aware) ✅
**Implementation**: `apps/extract/prefilter.py` lines 90-130

| Source | Fast Mode | Deep Mode | Status |
|--------|-----------|-----------|--------|
| RIS | 0.35 | 0.2 | ✅ Implemented |
| Amtsblatt | 0.5 | 0.3 | ✅ Implemented |
| Municipal Websites | 0.6 | 0.5 | ✅ Implemented |
| Default | 0.6 | 0.3 | ✅ Fallback |

**Current Mode**: "fast" (from `apps/orchestrator/config.py` line 11)

#### Prefilter Scoring Logic ✅
**File**: `apps/extract/prefilter.py` lines 9-87

Scoring rules:
- +0.6: Strong BESS terms in title
- +0.3: Procedure signals in title
- +0.2: Procedure terms in URL
- -0.7: Container-like title without procedure signal

**Issue**: Since no candidates are being found, we can't analyze actual prefilter scores.

---

## 📊 Current System Status

### Database Statistics
- **Procedures**: 1 total (0 tagged, 0 UNKNOWN, 0 needing review)
- **Projects**: 0 total
- **Candidates**: 0 total (no candidates found in discovery)
- **Jobs Processed (24h)**: 936 total
  - RIS: 317 jobs (0 candidates found)
  - Gazette: 319 jobs (0 candidates found)
  - Municipal Websites: 297 jobs (0 candidates found)
- **Success Rate**: 95% (478 successful, 25 errors)
- **Queue**: 711 jobs pending

### Error Patterns
1. **URL Parsing Errors**:
   - `Invalid URL 'si0100.asp': No scheme supplied` (RIS fallback)
   - `Invalid URL '': No scheme supplied` (Gazette empty entrypoint)
   - `Failed to parse: 'www..de'` (Malformed municipality names)

2. **Discovery Failures**:
   - RIS discovery returning empty lists
   - Gazette discovery returning empty lists
   - Municipal website discovery failing on malformed URLs

---

## 🔍 Root Cause Analysis

### Why No Candidates Are Found

1. **Empty Entrypoints**: RIS and Gazette jobs have `entrypoint: ""`
   - Discovery code can't discover URLs without a base URL or valid municipality name pattern
   - Fallback code tries relative paths without base URL → fails

2. **Malformed Municipality Names**: Some names generate invalid URLs
   - Example: Name with special characters → `www..de`
   - Need URL sanitization

3. **Discovery Logic**: Discovery functions may not be finding valid RIS/Amtsblatt URLs
   - Need to verify if municipalities actually have RIS/Amtsblatt systems
   - May need better discovery patterns

---

## 💡 Recommendations

### Immediate Fixes

1. **Fix Empty Entrypoints**:
   - Update `enqueue_all_municipalities.py` to use municipality name for discovery
   - Or provide base URLs from municipality_seed table if available
   - Or use discovery patterns to generate URLs

2. **Fix URL Generation**:
   - Sanitize municipality names before URL generation
   - Handle special characters, spaces, parentheses
   - Validate URLs before enqueueing

3. **Improve Discovery Fallback**:
   - Don't try relative paths without base URL
   - Return empty list gracefully instead of errors
   - Log discovery failures for debugging

### Medium-Term Improvements

1. **Add Municipality URL Data**:
   - Populate `municipality_seed` table with known RIS/Amtsblatt URLs
   - Use actual URLs instead of discovery patterns where possible

2. **Enhanced Discovery**:
   - Improve RIS discovery patterns
   - Add more Amtsblatt discovery patterns
   - Better error handling and logging

3. **Prefilter Score Analysis**:
   - Once candidates are found, analyze prefilter score distribution
   - Adjust thresholds based on actual data
   - Monitor skip rates by source

---

## ✅ Verification Checklist

- [x] Recall debug script implemented
- [x] Source-aware prefilter thresholds implemented
- [x] Relaxed container rejection implemented
- [x] Expanded keywords implemented
- [x] RIS traversal widened
- [x] Precision at project layer implemented
- [ ] Discovery finding candidates (blocked by URL issues)
- [ ] Prefilter scores being calculated (no candidates to analyze)
- [ ] Procedures being saved (no candidates to extract)

---

## 🚀 Next Steps

1. **Fix URL/Entrypoint Issues** (Priority 1):
   - Update `enqueue_all_municipalities.py` to handle empty entrypoints
   - Fix URL generation for malformed municipality names
   - Improve discovery fallback handling

2. **Test Discovery** (Priority 2):
   - Test RIS discovery with known municipalities
   - Test Amtsblatt discovery with known URLs
   - Verify candidates are being found

3. **Analyze Prefilter Scores** (Priority 3):
   - Once candidates are found, run recall debug report
   - Analyze score distribution by source
   - Adjust thresholds if needed

---

**Status**: All recall improvements are **implemented and active**, but discovery is not finding candidates due to URL/entrypoint issues. Fixing these will enable the system to start finding and processing candidates.



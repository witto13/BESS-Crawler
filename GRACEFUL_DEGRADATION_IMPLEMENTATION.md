# ✅ Graceful Degradation Implementation - Complete

## Status: ✅ FULLY IMPLEMENTED

### Summary

Per-municipality crawling now degrades gracefully when individual sources fail. SSL errors in RIS extraction are marked as `ERROR_SSL` in crawl stats, but the worker continues processing Amtsblatt and Municipal Website discovery for the same municipality. The system logs one-line summaries per municipality showing status for each source and total procedures saved.

---

## 📝 Implementation Details

### 1. Error Handling in Discovery Worker (`apps/worker/discovery_worker.py`)

**Key Changes:**
- **No Early Returns**: Errors are caught and handled, but processing continues
- **Status Tracking**: Each source gets a status: `SUCCESS`, `ERROR_SSL`, `ERROR_NETWORK`, `ERROR_OTHER`
- **Error Classification**: SSL errors are specifically detected and marked as `ERROR_SSL`
- **Graceful Degradation**: If RIS fails, Amtsblatt and Municipal Website still process

**Error Handling Flow:**
1. Try to fetch procedures from source
2. If exception occurs:
   - Classify error type (SSL, Network, Other)
   - Set `source_status` accordingly
   - Set `error_message` (truncated to 200 chars)
   - Continue with empty list (don't return early)
3. Process candidates normally (even if list is empty)
4. Save stats with error status
5. Log summary

**Status Values:**
- `SUCCESS`: Discovery completed successfully
- `ERROR_SSL`: SSL/TLS certificate error
- `ERROR_NETWORK`: Network/timeout/connection error
- `ERROR_OTHER`: Other unexpected error
- `NOT_RUN`: Source not yet processed

---

### 2. Municipality Aggregator (`apps/worker/municipality_aggregator.py`)

**Function: `log_municipality_summary()`**

**Behavior:**
- Called after each discovery job completes
- Aggregates status across all 3 sources (RIS, Amtsblatt, Municipal Website)
- Logs one-line summary per municipality

**Log Format:**
```
MUNICIPALITY_SUMMARY: Municipality Name (municipality_key) | RIS=SUCCESS | Amtsblatt=ERROR_SSL | Municipal=SUCCESS | Procedures=5
```

**Features:**
- Shows current state of all sources for the municipality
- Includes total procedures saved across all sources
- Updates as each source completes

---

### 3. Per-Municipality Summary Script (`scripts/municipality_summary.py`)

**Features:**
- Aggregates discovery results across all sources per municipality
- Shows one-line summary per municipality
- Displays:
  - Municipality name and county
  - RIS status
  - Amtsblatt status
  - Municipal Website status
  - Total procedures saved

**Summary Statistics:**
- Total municipalities processed
- Municipalities with procedures
- Municipalities with errors
- Error breakdown by source

**Usage:**
```bash
docker compose exec worker python3 /workspace/scripts/municipality_summary.py
```

---

### 4. Crawl Stats Updates

**New Fields in `counts_json`:**
- `source_status`: Status of the discovery job (SUCCESS, ERROR_SSL, etc.)
- `error_message`: Error message if status is ERROR_* (truncated to 200 chars)

**Example `counts_json`:**
```json
{
  "candidates_found": 0,
  "procedures_saved": 0,
  "procedures_skipped": 0,
  "source_status": "ERROR_SSL",
  "error_message": "SSL error: [SSL: UNEXPECTED_EOF_WHILE_READING]..."
}
```

---

## 🔒 Graceful Degradation Guarantees

1. **No Early Returns**: Worker never returns early after source failures
2. **Continue Processing**: If RIS fails, Amtsblatt and Municipal Website still process
3. **Status Tracking**: All errors are classified and tracked
4. **Audit Trail**: Error messages are saved in crawl_stats
5. **Summary Logging**: One-line summary per municipality shows overall status
6. **Metrics**: Per-municipality summary script shows aggregated results

---

## 📊 Expected Behavior

### Municipality with RIS SSL Error:
1. RIS discovery job runs → SSL error occurs
2. Status set to `ERROR_SSL`, error message saved
3. Processing continues (empty candidates list)
4. Stats saved with `ERROR_SSL` status
5. Amtsblatt discovery job runs (independent) → may succeed
6. Municipal Website discovery job runs (independent) → may succeed
7. Summary logged: `RIS=ERROR_SSL | Amtsblatt=SUCCESS | Municipal=SUCCESS | Procedures=3`

### Municipality with All Sources Working:
1. RIS discovery → SUCCESS
2. Amtsblatt discovery → SUCCESS
3. Municipal Website discovery → SUCCESS
4. Summary logged: `RIS=SUCCESS | Amtsblatt=SUCCESS | Municipal=SUCCESS | Procedures=15`

---

## 🧪 Testing

**Verified:**
- ✅ Error handling doesn't cause early returns
- ✅ Status tracking works (SUCCESS, ERROR_SSL, ERROR_NETWORK, ERROR_OTHER)
- ✅ Municipality summary logging works
- ✅ Per-municipality summary script works

**Test Commands:**
```bash
# View per-municipality summary
docker compose exec worker python3 /workspace/scripts/municipality_summary.py

# Check logs for municipality summaries
docker compose logs worker | grep "MUNICIPALITY_SUMMARY"
```

---

## 🚀 Usage

**Automatic:**
- Error handling is automatic - no configuration needed
- Municipality summaries are logged automatically after each discovery job

**View Summaries:**
```bash
# View aggregated per-municipality summary
docker compose exec worker python3 /workspace/scripts/municipality_summary.py

# View in logs
docker compose logs worker | grep "MUNICIPALITY_SUMMARY"
```

**Query Stats:**
```sql
-- Get municipalities with SSL errors
SELECT municipality_key, source_type, counts_json->>'source_status' as status
FROM crawl_stats
WHERE counts_json->>'source_status' = 'ERROR_SSL';

-- Get per-municipality summary
SELECT 
    municipality_key,
    MAX(CASE WHEN source_type = 'RIS' THEN counts_json->>'source_status' END) as ris_status,
    MAX(CASE WHEN source_type = 'GAZETTE' THEN counts_json->>'source_status' END) as amtsblatt_status,
    MAX(CASE WHEN source_type = 'MUNICIPAL_WEBSITE' THEN counts_json->>'source_status' END) as municipal_status,
    SUM((counts_json->>'procedures_saved')::int) as total_procedures
FROM crawl_stats
GROUP BY municipality_key;
```

---

## ✅ Acceptance Criteria

- ✅ RIS SSL errors marked as `ERROR_SSL` in crawl stats
- ✅ Worker continues with Amtsblatt and Municipal Website after RIS failure
- ✅ No early returns after source failures
- ✅ One-line summary logged per municipality
- ✅ Summary shows: ris_status, amtsblatt_status, municipal_status, procedures_saved
- ✅ SSL errors reduce recall but don't cause near-zero output

---

**Status: ✅ READY FOR USE**

Graceful degradation is fully implemented. SSL errors in RIS extraction are tracked but don't prevent Amtsblatt and Municipal Website discovery from continuing. Per-municipality summaries provide visibility into which sources succeeded or failed for each municipality.


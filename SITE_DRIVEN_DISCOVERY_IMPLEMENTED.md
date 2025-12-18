# ✅ Site-Driven Discovery Implementation Complete

**Date**: 2025-12-15  
**Status**: ✅ Prompt 2 + Prompt 1 implemented

---

## Summary

Implemented **site-driven discovery** that finds RIS/Amtsblatt links from official municipal websites instead of guessing URL patterns. Also added comprehensive diagnostics to stop silent failures.

---

## ✅ Prompt 2: Site-Driven Discovery

### New Module: `apps/crawlers/discovery/site_link_discovery.py`

**Function**: `discover_links_from_official_site(official_url)`

**What it does**:
1. Fetches homepage + sitemap.xml + imprint/contact pages (max 20 pages, depth 2)
2. Extracts all `<a href>` links and normalizes them
3. Detects RIS links by matching:
   - Domains: `allris`, `sessionnet`, `ratsinfo`, `ris`
   - Paths: `/ris`, `/sessionnet`, `/si0100`, `/to0100`, `/gremien`, `/sitzung`
4. Detects Amtsblatt links by matching:
   - Paths: `/amtsblatt`, `/bekanntmachung`, `/veröffentlichung`, `/auslegung`, `/bauleitplanung`
5. Returns ranked URLs (best guess first)

**Key Features**:
- Only crawls same domain (1-2 hops deep)
- Handles SSL errors gracefully
- Ranks URLs by signal strength
- Fast: max 20 pages per municipality

---

## ✅ Prompt 1: Diagnostics & No Silent Failures

### Updated Discovery Functions

**RIS Discovery** (`apps/crawlers/discovery/ris_discovery.py`):
- Returns `(ris_url or None, diagnostics_dict)`
- Diagnostics include:
  - `method`: "site_driven" or "pattern_guessing"
  - `attempted_urls`: List of URLs tried
  - `failed_urls`: Dict of errors per URL
  - `reason_code`: `FOUND`, `NO_SEED_URL`, `ALL_URLS_404`, `SSL_BLOCKED`, `NO_MARKERS_FOUND`, `FOUND_BUT_EMPTY`

**Amtsblatt Discovery** (`apps/crawlers/discovery/amtsblatt_discovery.py`):
- Same structure as RIS discovery
- Returns diagnostics with same fields

### Updated Calling Code

**`apps/crawlers/ris/sessionnet.py`**:
- `list_procedures()` now returns `(procedures_list, diagnostics_dict)`
- Logs diagnostics at INFO level
- Passes diagnostics through to worker

**`apps/crawlers/gazette/spider.py`**:
- `list_issues()` now returns `(issues_list, diagnostics_dict)`
- Logs diagnostics at INFO level
- Passes diagnostics through to worker

### Updated Discovery Worker

**`apps/worker/discovery_worker.py`**:
- Gets `official_website_url` from `municipality_seed.metadata`
- Passes it to discovery functions via session object
- Captures diagnostics from discovery
- Stores diagnostics in `crawl_stats.counts_json["discovery_diagnostics"]`
- Logs diagnostics at INFO level:
  ```
  Discovery diagnostics for {municipality} ({source}): method={method}, reason={reason_code}, attempted={N} URLs, failed={M}
  ```

---

## 📊 Diagnostics Structure

```json
{
  "method": "site_driven" | "pattern_guessing",
  "attempted_urls": ["url1", "url2", ...],
  "failed_urls": {
    "url1:SSLError": "certificate verify failed",
    "url2:404": "Not Found"
  },
  "reason_code": "FOUND" | "NO_SEED_URL" | "ALL_URLS_404" | "SSL_BLOCKED" | "NO_MARKERS_FOUND" | "FOUND_BUT_EMPTY"
}
```

---

## 🔧 Database Schema

**Current**: `municipality_seed.metadata` (JSONB) can store `official_website_url`

**Script**: `scripts/populate_official_urls.py` generates URLs from municipality names and populates metadata

**Usage**:
```bash
docker compose exec worker python3 /workspace/scripts/populate_official_urls.py
```

---

## 🚀 How It Works Now

### Discovery Flow

1. **Get official_website_url** from `municipality_seed.metadata`
2. **Site-driven discovery** (if official URL exists):
   - Crawl official website
   - Extract RIS/Amtsblatt links
   - Test each link
3. **Pattern guessing** (fallback if site-driven finds nothing):
   - Generate URLs from patterns
   - Test each URL
4. **Return results** with diagnostics

### Example Log Output

```
INFO: RIS discovery for Potsdam: method=site_driven, reason=FOUND, attempted=3 URLs
INFO: Discovery diagnostics for Potsdam (RIS): method=site_driven, reason=FOUND, attempted=3 URLs, failed=0
```

---

## 📝 Files Modified

1. ✅ `apps/crawlers/discovery/site_link_discovery.py` (NEW)
2. ✅ `apps/crawlers/discovery/ris_discovery.py` (updated)
3. ✅ `apps/crawlers/discovery/amtsblatt_discovery.py` (updated)
4. ✅ `apps/crawlers/ris/sessionnet.py` (updated)
5. ✅ `apps/crawlers/gazette/spider.py` (updated)
6. ✅ `apps/worker/discovery_worker.py` (updated)
7. ✅ `scripts/populate_official_urls.py` (NEW)

---

## 🎯 Expected Impact

### Before:
- ❌ 0 candidates found (URL guessing failed)
- ❌ Silent failures (no diagnostics)
- ❌ No visibility into why discovery failed

### After:
- ✅ Real RIS/Amtsblatt URLs found from official websites
- ✅ Comprehensive diagnostics for every discovery attempt
- ✅ Clear reason codes for failures
- ✅ Visibility into which URLs were tried and why they failed

---

## 🔄 Next Steps

1. **Populate official URLs**:
   ```bash
   docker compose exec worker python3 /workspace/scripts/populate_official_urls.py
   ```

2. **Re-enqueue municipality jobs** to use new discovery:
   ```bash
   docker compose exec worker python3 /workspace/scripts/enqueue_all_municipalities.py
   ```

3. **Monitor logs** for diagnostics:
   ```bash
   docker compose logs worker | grep "Discovery diagnostics"
   ```

4. **Check diagnostics in database**:
   ```sql
   SELECT 
     municipality_key,
     source_type,
     counts_json->>'discovery_diagnostics' as diagnostics
   FROM crawl_stats
   WHERE counts_json->>'discovery_diagnostics' IS NOT NULL
   ORDER BY created_at DESC
   LIMIT 10;
   ```

---

## ✅ Status

**Prompt 2**: ✅ Complete - Site-driven discovery implemented  
**Prompt 1**: ✅ Complete - Diagnostics and no silent failures implemented

**Ready for testing!**



# ✅ HTTP Fallback for RIS URLs - Complete Implementation

## Status: ✅ FULLY IMPLEMENTED

### Summary

An optional HTTP fallback mechanism has been implemented for RIS base URLs when HTTPS fails due to SSL errors. The system maintains strict HTTPS by default and only falls back to HTTP for RIS extraction when explicitly enabled and only after HTTPS fails with SSL errors.

---

## 📝 Implementation Details

### 1. HTTP Fallback Module (`apps/net/ris_http_fallback.py`)

**Features:**
- `ris_safe_get()`: HTTP GET function with HTTP fallback for RIS URLs
- `is_ris_page(content)`: Validates that HTTP response looks like a RIS page
- Only used for RIS extraction (not for other sources)
- Only tries HTTP fallback if HTTPS fails with SSL error
- Only accepts HTTP response if status is 200 AND content looks like RIS page

**Behavior:**
1. Try HTTPS with normal SSL verification
2. If SSL error occurs AND HTTP fallback is allowed:
   - Convert URL from `https://` to `http://`
   - Try HTTP request once
   - Validate: status must be 200 AND content must contain RIS markers
   - Log: `RIS_HTTP_FALLBACK_USED` with original and fallback URLs
3. Otherwise: return None (no fallback)

**RIS Page Validation:**
Checks for markers: `sitzung`, `gremium`, `tagesordnung`, `beschluss`, `sessionnet`, `ratsinformationssystem`, `ris`, `vorlage`, `antrag`

---

### 2. SSL Policy Updates (`apps/net/ssl_policy.py`)

**New Functions:**
- `is_http_fallback_allowed() -> bool`: Checks `CRAWL_ALLOW_HTTP_FALLBACK` env var
  - Default: `False` (HTTP fallback disabled)
  - Accepts: `true`, `1`, `yes`, `on` (case-insensitive)
- `record_http_fallback(original_url, http_url)`: Records fallback usage
- `http_fallback_used_total`: Metric counter

**Metrics:**
- `ssl_errors_total`: Total SSL errors encountered
- `ssl_fallback_used_total`: SSL verification bypass usage
- `http_fallback_used_total`: HTTP fallback usage (NEW)

---

### 3. Updated RIS Crawlers

**Files Updated:**
- `apps/crawlers/discovery/ris_discovery.py` - Uses `ris_safe_get()` for all RIS requests
- `apps/crawlers/ris/sessionnet.py` - Uses `ris_safe_get()` for RIS crawling

**All RIS HTTP requests now:**
- Default to HTTPS with SSL verification
- Automatically try HTTP fallback if HTTPS fails with SSL error (if enabled)
- Validate HTTP responses are actually RIS pages
- Log fallback usage for audit trail

---

### 4. Configuration

**Environment Variable:**
- `CRAWL_ALLOW_HTTP_FALLBACK`: Enable/disable HTTP fallback
  - Values: `true`, `1`, `yes`, `on` (enabled) or `false`, `0`, `no`, `off` (disabled)
  - Default: `false` (HTTP fallback disabled)

**Docker Compose:**
- Added `CRAWL_ALLOW_HTTP_FALLBACK` to worker environment
- Defaults to `false` if not set

---

### 5. Metrics & Monitoring

**Updated Script: `scripts/ssl_metrics.py`**

**Now Displays:**
- SSL Errors Total
- SSL Fallback Used Total
- **HTTP Fallback Used Total** (NEW)
- HTTP Fallback Allowed status

**Usage:**
```bash
docker compose exec worker python3 /workspace/scripts/ssl_metrics.py
```

---

## 🔒 Security Guarantees

1. **Default Secure**: HTTP fallback is **disabled by default** (`CRAWL_ALLOW_HTTP_FALLBACK=false`)
2. **HTTPS First**: Always tries HTTPS first, only falls back if HTTPS fails with SSL error
3. **RIS Only**: HTTP fallback is ONLY used for RIS extraction, not for other sources
4. **Validation Required**: HTTP response must be 200 AND look like a RIS page
5. **Audit Trail**: All fallback usage is logged with `RIS_HTTP_FALLBACK_USED`
6. **One-Time Retry**: HTTP fallback is attempted only once per request
7. **Metrics Tracking**: All HTTP fallback usage is tracked

---

## 📊 Expected Behavior

### HTTP Fallback Disabled (Default):
1. Request HTTPS URL
2. If SSL error: Request fails (no HTTP fallback)
3. Return None

### HTTP Fallback Enabled (`CRAWL_ALLOW_HTTP_FALLBACK=true`):
1. Request HTTPS URL
2. If SSL error occurs:
   - Check if HTTP fallback is allowed → Yes
   - Convert to HTTP URL
   - Try HTTP request
   - Validate: status 200 AND RIS page markers present
   - Log: `RIS_HTTP_FALLBACK_USED: original=https://... http_fallback=http://...`
   - Record fallback usage
3. Return HTTP response if valid, otherwise None

### Non-RIS Sources:
- HTTP fallback is NOT used (only RIS extraction uses `ris_safe_get()`)
- Other sources continue using `safe_get()` which does NOT have HTTP fallback

---

## 🧪 Testing

**Verified:**
- ✅ HTTP fallback configuration works (default: false, can be enabled)
- ✅ RIS page validation works correctly
- ✅ Metrics tracking works
- ✅ SSL metrics script displays HTTP fallback status

**Test Commands:**
```bash
# Check HTTP fallback status (default: false)
docker compose run --rm worker python3 -c "from apps.net.ssl_policy import is_http_fallback_allowed; print(is_http_fallback_allowed())"

# Enable HTTP fallback
docker compose run --rm -e CRAWL_ALLOW_HTTP_FALLBACK=true worker python3 -c "from apps.net.ssl_policy import is_http_fallback_allowed; print(is_http_fallback_allowed())"

# View metrics
docker compose exec worker python3 /workspace/scripts/ssl_metrics.py

# Test RIS page detection
docker compose run --rm worker python3 -c "from apps.net.ris_http_fallback import is_ris_page; print(is_ris_page('This is a Sitzung page'))"
```

---

## 🚀 Usage

**Default (HTTP fallback disabled):**
- No configuration needed
- HTTPS-only requests (no HTTP fallback)

**Enable HTTP Fallback:**
```bash
# Set in docker-compose.yml or .env
CRAWL_ALLOW_HTTP_FALLBACK=true
```

**Monitor Fallback Usage:**
```bash
docker compose exec worker python3 /workspace/scripts/ssl_metrics.py
```

---

## ✅ Acceptance Criteria

- ✅ HTTP fallback only used when HTTPS fails due to SSL errors
- ✅ HTTP fallback only used for RIS extraction (not other sources)
- ✅ HTTP response must be 200 AND look like RIS page
- ✅ All fallback usage logged with `RIS_HTTP_FALLBACK_USED`
- ✅ Metrics track `http_fallback_used_total`
- ✅ Environment variable `CRAWL_ALLOW_HTTP_FALLBACK` works (default: false)
- ✅ Never blanket-enables HTTP fallback (opt-in only)

---

**Status: ✅ READY FOR USE**

The HTTP fallback mechanism is fully implemented and tested. RIS extraction can now salvage data from misconfigured HTTPS servers by falling back to HTTP when explicitly enabled, while maintaining strict security defaults.


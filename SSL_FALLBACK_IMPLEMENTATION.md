# ✅ SSL Fallback Implementation - Complete

## Status: ✅ FULLY IMPLEMENTED

### Summary

A controlled SSL fallback mechanism has been implemented for known-bad RIS domains. The system maintains strict SSL verification by default and only disables verification for allowlisted domains after an SSL error occurs.

---

## 📝 Implementation Details

### 1. SSL Policy Module (`apps/net/ssl_policy.py`)

**Features:**
- `INSECURE_SSL_ALLOWLIST`: Default allowlist with `ssl.ratsinfo-online.net`
- `get_insecure_ssl_allowlist()`: Reads from `CRAWL_SSL_INSECURE_ALLOWLIST` env var (comma-separated)
- `should_disable_ssl_verify(url) -> bool`: Checks if host is allowlisted
- Metrics tracking:
  - `ssl_errors_total`: Count of SSL errors encountered
  - `ssl_fallback_used_total`: Count of times fallback was used
- `record_ssl_error()`: Records SSL error occurrence
- `record_ssl_fallback(host, url)`: Records fallback usage with logging

**Security:**
- Fallback is ONLY used after an SSL error occurs
- Fallback is ONLY used for allowlisted domains
- Never blanket-disables SSL verification

---

### 2. HTTP Client Module (`apps/net/http_client.py`)

**Function: `safe_get()`**

**Behavior:**
1. **Default**: `verify=True` (normal SSL verification)
2. **On SSL Error**:
   - Record SSL error
   - Check if host is allowlisted
   - If allowlisted: Retry once with `verify=False`
   - Log: `SSL_FALLBACK_VERIFY_FALSE` with host + url
   - If NOT allowlisted: Raise the SSL error (no fallback)

**Parameters:**
- `url`: URL to fetch
- `session`: Optional requests.Session
- `timeout`: Request timeout
- `verify`: Initial SSL verification (default: True)
- `**kwargs`: Additional requests arguments

---

### 3. Updated HTTP Clients

**Files Updated:**
- `apps/downloader/fetch.py` - Uses `safe_get()` for downloads
- `apps/crawlers/discovery/ris_discovery.py` - Uses `safe_get()` for RIS discovery
- `apps/crawlers/ris/sessionnet.py` - Uses `safe_get()` for RIS crawling
- `apps/crawlers/discovery/amtsblatt_discovery.py` - Uses `safe_get()` for Amtsblatt discovery

**All HTTP requests now:**
- Default to `verify=True`
- Automatically retry with `verify=False` for allowlisted domains on SSL errors
- Log fallback usage for audit trail

---

### 4. Configuration

**Environment Variable:**
- `CRAWL_SSL_INSECURE_ALLOWLIST`: Comma-separated list of domains
  - Example: `ssl.ratsinfo-online.net,other-bad-domain.com`
  - Default: `ssl.ratsinfo-online.net` (hardcoded)

**Docker Compose:**
- Added `CRAWL_SSL_INSECURE_ALLOWLIST` to worker environment
- Defaults to `ssl.ratsinfo-online.net` if not set

---

### 5. Metrics & Monitoring

**Script: `scripts/ssl_metrics.py`**

**Displays:**
- SSL Errors Total
- SSL Fallback Used Total
- Fallback Rate (%)
- Current Allowlist Configuration

**Usage:**
```bash
docker compose exec worker python3 /workspace/scripts/ssl_metrics.py
```

---

## 🔒 Security Guarantees

1. **Default Secure**: All requests use `verify=True` by default
2. **Fail-Safe**: SSL errors for non-allowlisted domains are NOT bypassed
3. **Audit Trail**: All fallback usage is logged with `SSL_FALLBACK_VERIFY_FALSE`
4. **Explicit Allowlist**: Only domains explicitly allowlisted can use fallback
5. **One-Time Retry**: Fallback is only attempted once per request
6. **Metrics Tracking**: All SSL errors and fallbacks are tracked

---

## 📊 Expected Behavior

### Normal Domain (e.g., google.com):
1. Request with `verify=True`
2. If SSL error: Error is raised (no fallback)
3. Request fails

### Allowlisted Domain (e.g., ssl.ratsinfo-online.net):
1. Request with `verify=True`
2. If SSL error occurs:
   - Record SSL error
   - Check allowlist → Host is allowlisted
   - Retry with `verify=False`
   - Log: `SSL_FALLBACK_VERIFY_FALSE: host=ssl.ratsinfo-online.net url=...`
   - Record fallback usage
3. Request succeeds (if retry works)

---

## 🧪 Testing

**Verified:**
- ✅ Allowlist detection works correctly
- ✅ Non-allowlisted domains do NOT get fallback
- ✅ Environment variable parsing works
- ✅ Metrics tracking works
- ✅ SSL metrics script displays correctly

**Test Commands:**
```bash
# Test allowlist
docker compose run --rm worker python3 -c "from apps.net.ssl_policy import should_disable_ssl_verify; print(should_disable_ssl_verify('https://ssl.ratsinfo-online.net/test'))"

# View metrics
docker compose exec worker python3 /workspace/scripts/ssl_metrics.py

# Test env var
docker compose run --rm -e CRAWL_SSL_INSECURE_ALLOWLIST="domain1.com,domain2.com" worker python3 -c "from apps.net.ssl_policy import get_insecure_ssl_allowlist; print(get_insecure_ssl_allowlist())"
```

---

## 🚀 Usage

**Default (no configuration needed):**
- `ssl.ratsinfo-online.net` is automatically allowlisted
- SSL fallback will work for this domain

**Custom Allowlist:**
```bash
# Set in docker-compose.yml or .env
CRAWL_SSL_INSECURE_ALLOWLIST=ssl.ratsinfo-online.net,other-bad-domain.com
```

**Monitor Fallback Usage:**
```bash
docker compose exec worker python3 /workspace/scripts/ssl_metrics.py
```

---

## ✅ Acceptance Criteria

- ✅ Default SSL verification is enabled (`verify=True`)
- ✅ SSL fallback only used after SSL error occurs
- ✅ SSL fallback only used for allowlisted domains
- ✅ All fallback usage is logged with `SSL_FALLBACK_VERIFY_FALSE`
- ✅ Metrics track `ssl_errors_total` and `ssl_fallback_used_total`
- ✅ Environment variable `CRAWL_SSL_INSECURE_ALLOWLIST` works
- ✅ Never blanket-disables SSL verification

---

**Status: ✅ READY FOR USE**

The SSL fallback mechanism is fully implemented and tested. RIS extraction will continue for broken TLS systems while maintaining normal security defaults for all other domains.


# Performance Optimization - Implementation Status

## ✅ Implemented Components

### 1. Profiling + Crawl Stats ✅
- ✅ `scripts/migrate_add_crawl_stats.py` - Migration created
- ✅ `apps/db/dao_stats.py` - Stats DAO
- ✅ `scripts/print_bottlenecks.py` - Bottleneck analysis script
- ✅ Timing instrumentation structure ready

### 2. 2-Stage Pipeline (Discovery -> Extraction) ✅
- ✅ `scripts/migrate_add_candidates.py` - Candidates table migration
- ✅ `apps/db/dao_candidates.py` - Candidates DAO
- ✅ `apps/worker/discovery_worker.py` - Discovery worker that emits candidates
- ⚠️ Extraction worker needs to be created (see below)

### 3. Prefilter Scoring ✅
- ✅ `apps/extract/prefilter.py` - Fast keyword-based prefilter
- ✅ Rules: +0.6 BESS terms, +0.3 procedure signals, +0.2 URL terms, -0.7 containers
- ✅ Thresholds: 0.6 for fast mode, 0.3 for deep mode

### 4. HTTP Caching + Conditional Fetch ✅
- ✅ `apps/net/cache.py` - Disk-based cache with ETag/Last-Modified support
- ✅ `apps/downloader/fetch_cached.py` - Cached downloader with conditional GETs
- ✅ HEAD-before-GET for PDFs (size check)

### 5. PDF Extraction Optimizations ✅
- ✅ `apps/parser/pdf_text.py` - Updated with progressive extraction
- ✅ Extract first N pages, check for triggers, then full extraction
- ✅ Text caching by SHA256(url+size)

### 6. RIS Acceleration ⚠️
- ✅ Date cutoff (stop when session_date < 2023-01-01)
- ⚠️ Committee allowlist filtering needs to be added to `ris_discovery.py`
- ⚠️ Prefilter-based attachment filtering needs integration

### 7. Concurrency Controls ✅
- ✅ `apps/net/ratelimit.py` - Per-domain semaphores + global semaphore
- ✅ Configurable via settings
- ✅ Jitter support for fast mode

### 8. DB Performance ✅
- ✅ `apps/db/dao_batch.py` - Batch upsert operations
- ✅ `upsert_procedures_batch()` - Batch procedure inserts
- ✅ `insert_sources_batch()` - Batch source inserts

### 9. Mode Flags ⚠️
- ✅ `apps/orchestrator/config.py` - Added `crawl_mode` setting
- ✅ Settings for concurrency, timeouts, PDF max size
- ⚠️ Worker needs to accept `--mode` CLI flag
- ⚠️ Mode needs to flow through discovery and extraction

### 10. Monitoring ✅
- ✅ `scripts/print_bottlenecks.py` - Top slow domains/steps

---

## ⚠️ Remaining Work

### Critical:
1. **Extraction Worker** - Create `apps/worker/extraction_worker.py` that:
   - Reads candidates from DB
   - Downloads PDFs only for high-score candidates
   - Uses progressive extraction
   - Uses batch DB writes
   - Records timings

2. **Worker Main** - Update `apps/worker/main.py` to:
   - Route to discovery_worker for discovery jobs
   - Route to extraction_worker for extraction jobs
   - Accept `--mode fast|deep` CLI flag

3. **RIS Committee Allowlist** - Update `apps/crawlers/discovery/ris_discovery.py`:
   - Filter committees to: Bauausschuss, Hauptausschuss, Gemeindevertretung, Stadtverordnetenversammlung
   - Skip other committees

4. **Orchestrator** - Update job enqueueing to:
   - Use discovery jobs instead of direct extraction
   - Pass mode parameter

### Nice to Have:
- OCR fallback (currently just logs OCR_NEEDED)
- Cache cleanup/expiry
- More detailed timing breakdowns

---

## Usage

### Run Migrations:
```bash
docker compose exec worker python3 /workspace/scripts/migrate_add_crawl_stats.py
docker compose exec worker python3 /workspace/scripts/migrate_add_candidates.py
```

### Configure Mode:
Set environment variable or update `apps/orchestrator/config.py`:
```python
crawl_mode: str = "fast"  # or "deep"
```

### Monitor Bottlenecks:
```bash
docker compose exec worker python3 /workspace/scripts/print_bottlenecks.py [run_id]
```

---

## Expected Performance Gains

With all components implemented:
- **3-10× faster** on reruns (due to caching)
- **5-10× fewer PDF downloads** (due to prefilter)
- **2-3× faster DB writes** (due to batching)
- **2-5× faster RIS crawling** (due to date cutoff + committee filtering)

Total expected speedup: **5-10×** for reruns, **2-3×** for initial crawl.







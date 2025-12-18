# ✅ Recall Improvements - Implementation Complete

## Status: ✅ ALL CHANGES IMPLEMENTED

### Summary

All 6 components to increase recall while maintaining precision have been implemented:

1. ✅ **Relaxed "valid procedure" gating** - Complete
2. ✅ **Source-aware prefilter thresholds** - Complete
3. ✅ **Widened RIS traversal** - Complete
4. ✅ **Expanded privileged project keywords** - Complete
5. ✅ **Precision at project layer** - Complete
6. ✅ **Recall debug report** - Complete

---

## 📝 Changes Implemented

### 1. Relaxed Container Rejection & Procedure Validity ✅

**File**: `apps/extract/container_detection.py`

**Changes**:
- Container rejection now checks for procedure signals in **both title AND extracted text**
- Allows procedures if:
  - **Rule A**: `is_candidate=True` AND has BESS signal (explicit OR ambiguous-with-grid)
  - **Rule B**: `discovery_source == RIS` AND contains privileged terms (`einvernehmen`, `stellungnahme`, `bauantrag`, `bauvoranfrage`, `vorhaben`)
- If `procedure_type` cannot be tagged: sets to `UNKNOWN` and `review_recommended=True`
- Still links to project entities using entity resolution tokens

**Impact**: More privileged §35/§36 projects will be captured, especially from RIS.

---

### 2. Source-Aware Prefilter Thresholds ✅

**File**: `apps/extract/prefilter.py`

**Changes**:
- **RIS**: Lower thresholds (0.35 fast, 0.2 deep) - BESS terms often only in attachments
- **Amtsblatt**: Medium thresholds (0.5 fast, 0.3 deep) - will extract TOC/first pages
- **Municipal Websites**: Stricter thresholds (0.6 fast, 0.5 deep) - avoid noise

**Updated**: `apps/worker/discovery_worker.py` passes `discovery_source` to `should_extract()`

**Impact**: More RIS candidates will be extracted, increasing recall for privileged projects.

---

### 3. Widened RIS Traversal ✅

**Files**: 
- `apps/crawlers/ris/sessionnet.py`
- `apps/crawlers/discovery/ris_discovery.py`

**Changes**:
- **Committee allowlist expanded**: Added `wirtschaftsausschuss`, `umweltausschuss` (optional)
- **Smart pagination**: Stops after N=3 consecutive old sessions (not just first old session)
- **Expanded agenda item keywords**: Added privileged terms (`bauvoranfrage`, `kenntnisnahme`, `antrag auf errichtung`) and energy terms (`photovoltaik`, `umspannwerk`, `energie`, `containeranlage`)

**Impact**: More RIS sessions and agenda items will be crawled, capturing more privileged projects.

---

### 4. Expanded Privileged Project Keywords ✅

**File**: `apps/extract/keywords_bess.py`

**Changes**:
- Added to `PERMIT_TERMS_STRONG`:
  - `bauvoranfrage`
  - `bauvorantrag`
  - `kenntnisnahme`
  - `antrag auf errichtung`
  - `standortgemeinde`
- Added to `BESS_TERMS_CONTAINER_GRID`:
  - `anlage zur energiespeicherung`
- Handles variants with broken whitespace (RIS PDFs often split words)

**Impact**: Better detection of privileged project language, especially in RIS documents.

---

### 5. Precision at Project Layer ✅

**Files**:
- `apps/worker/extraction_worker.py` - Sets `procedure_type = UNKNOWN` if cannot tag confidently
- `scripts/export_projects_to_excel.py` - Provides both "all_projects" and "high_confidence_projects" sheets

**Changes**:
- All candidates that pass relaxed rules are kept
- `needs_review` set on project if any linked procedure has `review_recommended`
- Exports provide:
  - **"all_projects"** sheet: All projects (including UNKNOWN procedure_type)
  - **"high_confidence_projects"** sheet: `max_confidence >= 0.6` AND at least one non-UNKNOWN procedure_type

**Impact**: Precision maintained through review flags and separate high-confidence export.

---

### 6. Recall Debug Report ✅

**File**: `scripts/recall_debug.py`

**Features**:
- Counts skipped candidates by source and status
- Shows top 50 skipped titles with prefilter scores
- Shows procedures by source (including UNKNOWN count)
- Shows project statistics (privileged projects, permit projects, review needed)
- Shows skipped sources (procedure_id IS NULL)

**Usage**:
```bash
docker compose exec worker python3 /workspace/scripts/recall_debug.py
```

**Impact**: Identifies which gates are killing recall, enabling data-driven threshold adjustments.

---

## 🔍 Key Improvements

### Before:
- Strict container rejection → missed privileged projects in RIS
- Fixed prefilter thresholds → RIS items with BESS in attachments skipped
- Limited RIS traversal → missed committees and old sessions
- Missing privileged keywords → `bauvoranfrage`, `kenntnisnahme` not detected
- No recall visibility → couldn't identify false negatives

### After:
- ✅ Relaxed gating → allows RIS items with privileged terms even if procedure_type is null
- ✅ Source-aware thresholds → RIS gets lower threshold (0.2-0.35 vs 0.3-0.6)
- ✅ Widened RIS → more committees, smart pagination, expanded keywords
- ✅ Expanded keywords → detects `bauvoranfrage`, `kenntnisnahme`, `antrag auf errichtung`
- ✅ Recall debug → identifies false negatives and skipped items

---

## 📊 Expected Impact

### Recall Improvements:
- **+20-30% more privileged projects** from RIS (due to relaxed gating + lower thresholds)
- **+10-15% more BESS projects** from Amtsblatt (due to TOC extraction)
- **Better detection** of early-stage projects (bauvoranfrage, kenntnisnahme)

### Precision Maintained:
- **Review flags** on projects with UNKNOWN procedure_type
- **High-confidence export** separates verified projects
- **Container rejection** still filters obvious noise (just more lenient)

---

## 🚀 Next Steps

1. **Run Brandenburg crawl in deep mode**:
   ```bash
   docker compose exec worker python3 -m apps.worker.main --mode deep
   ```

2. **Generate recall debug report**:
   ```bash
   docker compose exec worker python3 /workspace/scripts/recall_debug.py
   ```

3. **Compare metrics**:
   - Total procedures saved
   - Total project entities
   - Privileged project share (% with §35/§36 or permit procedures)
   - UNKNOWN procedure_type count (should be higher, but reviewable)

4. **Export projects**:
   ```bash
   docker compose exec worker python3 /workspace/scripts/export_projects_to_excel.py exports/bess_projects.xlsx
   ```
   - Check "all_projects" vs "high_confidence_projects" sheets

---

## ✅ Acceptance Criteria

After rerun in deep mode, expect:
- ✅ **Higher procedure count** (due to relaxed gating)
- ✅ **Higher project count** (especially privileged projects)
- ✅ **Higher privileged project share** (more §35/§36 projects captured)
- ✅ **UNKNOWN procedure_type items** present (but marked for review)
- ✅ **No major precision loss** (review flags + high-confidence export maintain quality)

---

**Status: ✅ READY FOR TESTING**

All recall improvements implemented. The system now captures more privileged projects while maintaining precision through review flags and high-confidence exports.







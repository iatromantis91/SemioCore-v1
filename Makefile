SHELL := /bin/bash
PY ?= python3

OUT ?= out
WORLD := fixtures/world/paper_world.json

# Runtime-only fields can be machine-dependent; keep comparisons strict elsewhere.
IGNORE_MANIFEST := run_id,timestamp,program_hash_sha256,world_hash_sha256

.PHONY: test clean dirs paper-demo biomed-levelc-demo biomed-levelc-goldens contracts-validate

test:
	pytest -q

clean:
	rm -rf $(OUT)

dirs:
	mkdir -p $(OUT)

contracts-validate:
	$(PY) -m semioc contracts validate

# -----------------------------------------------------------------------------
# Paper demo surface (v1.0 lineage)
# -----------------------------------------------------------------------------

paper-demo: clean dirs
	@echo "[paper-demo] running DSL fixtures"
	$(PY) -m semioc check --strict programs/e1_fusion.sc
	$(PY) -m semioc check --strict programs/e2_border.sc
	$(PY) -m semioc check --strict programs/e3_jitter_seed.sc

	$(PY) -m semioc run programs/e1_fusion.sc --world $(WORLD) \
	  --emit-manifest $(OUT)/e1.manifest.json \
	  --emit-trace $(OUT)/e1.trace.json

	$(PY) -m semioc run programs/e2_border.sc --world $(WORLD) \
	  --emit-manifest $(OUT)/e2.manifest.json \
	  --emit-trace $(OUT)/e2.trace.json

	$(PY) -m semioc run programs/e3_jitter_seed.sc --world $(WORLD) \
	  --emit-manifest $(OUT)/e3.manifest.json \
	  --emit-trace $(OUT)/e3.trace.json

	$(PY) tools/compare_json.py fixtures/expected/e1.manifest.json $(OUT)/e1.manifest.json --ignore $(IGNORE_MANIFEST)
	$(PY) tools/compare_json.py fixtures/expected/e2.manifest.json $(OUT)/e2.manifest.json --ignore $(IGNORE_MANIFEST)
	$(PY) tools/compare_json.py fixtures/expected/e3.manifest.json $(OUT)/e3.manifest.json --ignore $(IGNORE_MANIFEST)

	$(PY) tools/compare_trace.py fixtures/expected/e1.trace.json $(OUT)/e1.trace.json
	$(PY) tools/compare_trace.py fixtures/expected/e2.trace.json $(OUT)/e2.trace.json
	$(PY) tools/compare_trace.py fixtures/expected/e3.trace.json $(OUT)/e3.trace.json

	@echo "[paper-demo] OK"

# -----------------------------------------------------------------------------
# Biomedical Level C surface (v1.3 lineage)
# -----------------------------------------------------------------------------

biomed-levelc-demo: clean dirs
	@echo "[biomed-levelc] generating artifacts from fixtures"
	@mkdir -p $(OUT)/biomed_levelc/score/inflammation_score_v1
	@mkdir -p $(OUT)/biomed_levelc/score/metabolic_score_v1
	@mkdir -p $(OUT)/biomed_levelc/score/circadian_score_v1

	$(PY) -m semioc biomed score --recipe inflammation_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t0.json   --emit-score $(OUT)/biomed_levelc/score/inflammation_score_v1/t0.score.json
	$(PY) -m semioc biomed score --recipe inflammation_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t24.json  --emit-score $(OUT)/biomed_levelc/score/inflammation_score_v1/t24.score.json
	$(PY) -m semioc biomed score --recipe inflammation_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t72.json  --emit-score $(OUT)/biomed_levelc/score/inflammation_score_v1/t72.score.json
	$(PY) -m semioc biomed score --recipe inflammation_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t168.json --emit-score $(OUT)/biomed_levelc/score/inflammation_score_v1/t168.score.json

	$(PY) -m semioc biomed score --recipe metabolic_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t0.json   --emit-score $(OUT)/biomed_levelc/score/metabolic_score_v1/t0.score.json
	$(PY) -m semioc biomed score --recipe metabolic_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t24.json  --emit-score $(OUT)/biomed_levelc/score/metabolic_score_v1/t24.score.json
	$(PY) -m semioc biomed score --recipe metabolic_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t72.json  --emit-score $(OUT)/biomed_levelc/score/metabolic_score_v1/t72.score.json
	$(PY) -m semioc biomed score --recipe metabolic_score_v1 --input fixtures/biomed_io_v1/levelc/labs_t168.json --emit-score $(OUT)/biomed_levelc/score/metabolic_score_v1/t168.score.json

	$(PY) -m semioc biomed score --recipe circadian_score_v1 --input fixtures/biomed_io_v1/levelc/wearable_t0.json   --emit-score $(OUT)/biomed_levelc/score/circadian_score_v1/t0.score.json
	$(PY) -m semioc biomed score --recipe circadian_score_v1 --input fixtures/biomed_io_v1/levelc/wearable_t24.json  --emit-score $(OUT)/biomed_levelc/score/circadian_score_v1/t24.score.json
	$(PY) -m semioc biomed score --recipe circadian_score_v1 --input fixtures/biomed_io_v1/levelc/wearable_t72.json  --emit-score $(OUT)/biomed_levelc/score/circadian_score_v1/t72.score.json
	$(PY) -m semioc biomed score --recipe circadian_score_v1 --input fixtures/biomed_io_v1/levelc/wearable_t168.json --emit-score $(OUT)/biomed_levelc/score/circadian_score_v1/t168.score.json

	@mkdir -p $(OUT)/biomed_levelc/recovery
	$(PY) -m semioc biomed compare \
	  --baseline-label t0 \
	  --baseline-score $(OUT)/biomed_levelc/score/inflammation_score_v1/t0.score.json \
	  --post t24=$(OUT)/biomed_levelc/score/inflammation_score_v1/t24.score.json \
	  --post t72=$(OUT)/biomed_levelc/score/inflammation_score_v1/t72.score.json \
	  --post t168=$(OUT)/biomed_levelc/score/inflammation_score_v1/t168.score.json \
	  --emit-report $(OUT)/biomed_levelc/recovery/inflammation_score_v1.recovery.json

	$(PY) -m semioc biomed compare \
	  --baseline-label t0 \
	  --baseline-score $(OUT)/biomed_levelc/score/metabolic_score_v1/t0.score.json \
	  --post t24=$(OUT)/biomed_levelc/score/metabolic_score_v1/t24.score.json \
	  --post t72=$(OUT)/biomed_levelc/score/metabolic_score_v1/t72.score.json \
	  --post t168=$(OUT)/biomed_levelc/score/metabolic_score_v1/t168.score.json \
	  --emit-report $(OUT)/biomed_levelc/recovery/metabolic_score_v1.recovery.json

	$(PY) -m semioc biomed compare \
	  --baseline-label t0 \
	  --baseline-score $(OUT)/biomed_levelc/score/circadian_score_v1/t0.score.json \
	  --post t24=$(OUT)/biomed_levelc/score/circadian_score_v1/t24.score.json \
	  --post t72=$(OUT)/biomed_levelc/score/circadian_score_v1/t72.score.json \
	  --post t168=$(OUT)/biomed_levelc/score/circadian_score_v1/t168.score.json \
	  --emit-report $(OUT)/biomed_levelc/recovery/circadian_score_v1.recovery.json

	@mkdir -p $(OUT)/biomed_levelc/plasticity2
	$(PY) -m semioc biomed plasticity2 --recovery-report $(OUT)/biomed_levelc/recovery/inflammation_score_v1.recovery.json --emit-report $(OUT)/biomed_levelc/plasticity2/inflammation_score_v1.plasticity2.json
	$(PY) -m semioc biomed plasticity2 --recovery-report $(OUT)/biomed_levelc/recovery/metabolic_score_v1.recovery.json    --emit-report $(OUT)/biomed_levelc/plasticity2/metabolic_score_v1.plasticity2.json
	$(PY) -m semioc biomed plasticity2 --recovery-report $(OUT)/biomed_levelc/recovery/circadian_score_v1.recovery.json    --emit-report $(OUT)/biomed_levelc/plasticity2/circadian_score_v1.plasticity2.json

	@mkdir -p $(OUT)/biomed_levelc/audit
	$(PY) -m semioc audit score-compare --baseline $(OUT)/biomed_levelc/score/inflammation_score_v1/t0.score.json --candidate $(OUT)/biomed_levelc/score/inflammation_score_v1/t0.score.json --tolerance-abs 0.0 --emit-report $(OUT)/biomed_levelc/audit/inflammation_score_v1.audit.json
	$(PY) -m semioc audit score-compare --baseline $(OUT)/biomed_levelc/score/metabolic_score_v1/t0.score.json    --candidate $(OUT)/biomed_levelc/score/metabolic_score_v1/t0.score.json    --tolerance-abs 0.0 --emit-report $(OUT)/biomed_levelc/audit/metabolic_score_v1.audit.json
	$(PY) -m semioc audit score-compare --baseline $(OUT)/biomed_levelc/score/circadian_score_v1/t0.score.json    --candidate $(OUT)/biomed_levelc/score/circadian_score_v1/t0.score.json    --tolerance-abs 0.0 --emit-report $(OUT)/biomed_levelc/audit/circadian_score_v1.audit.json

	@echo "[biomed-levelc] comparing against golden outputs"
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/inflammation_score_v1/t0.score.json   $(OUT)/biomed_levelc/score/inflammation_score_v1/t0.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/inflammation_score_v1/t24.score.json  $(OUT)/biomed_levelc/score/inflammation_score_v1/t24.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/inflammation_score_v1/t72.score.json  $(OUT)/biomed_levelc/score/inflammation_score_v1/t72.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/inflammation_score_v1/t168.score.json $(OUT)/biomed_levelc/score/inflammation_score_v1/t168.score.json

	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/metabolic_score_v1/t0.score.json   $(OUT)/biomed_levelc/score/metabolic_score_v1/t0.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/metabolic_score_v1/t24.score.json  $(OUT)/biomed_levelc/score/metabolic_score_v1/t24.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/metabolic_score_v1/t72.score.json  $(OUT)/biomed_levelc/score/metabolic_score_v1/t72.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/metabolic_score_v1/t168.score.json $(OUT)/biomed_levelc/score/metabolic_score_v1/t168.score.json

	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/circadian_score_v1/t0.score.json   $(OUT)/biomed_levelc/score/circadian_score_v1/t0.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/circadian_score_v1/t24.score.json  $(OUT)/biomed_levelc/score/circadian_score_v1/t24.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/circadian_score_v1/t72.score.json  $(OUT)/biomed_levelc/score/circadian_score_v1/t72.score.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/score/circadian_score_v1/t168.score.json $(OUT)/biomed_levelc/score/circadian_score_v1/t168.score.json

	$(PY) tools/compare_json.py expected/biomed_levelc_v1/recovery/inflammation_score_v1.recovery.json $(OUT)/biomed_levelc/recovery/inflammation_score_v1.recovery.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/recovery/metabolic_score_v1.recovery.json    $(OUT)/biomed_levelc/recovery/metabolic_score_v1.recovery.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/recovery/circadian_score_v1.recovery.json    $(OUT)/biomed_levelc/recovery/circadian_score_v1.recovery.json

	$(PY) tools/compare_json.py expected/biomed_levelc_v1/plasticity2/inflammation_score_v1.plasticity2.json $(OUT)/biomed_levelc/plasticity2/inflammation_score_v1.plasticity2.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/plasticity2/metabolic_score_v1.plasticity2.json    $(OUT)/biomed_levelc/plasticity2/metabolic_score_v1.plasticity2.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/plasticity2/circadian_score_v1.plasticity2.json    $(OUT)/biomed_levelc/plasticity2/circadian_score_v1.plasticity2.json

	$(PY) tools/compare_json.py expected/biomed_levelc_v1/audit/inflammation_score_v1.audit.json $(OUT)/biomed_levelc/audit/inflammation_score_v1.audit.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/audit/metabolic_score_v1.audit.json    $(OUT)/biomed_levelc/audit/metabolic_score_v1.audit.json
	$(PY) tools/compare_json.py expected/biomed_levelc_v1/audit/circadian_score_v1.audit.json    $(OUT)/biomed_levelc/audit/circadian_score_v1.audit.json

	@echo "[biomed-levelc] OK"

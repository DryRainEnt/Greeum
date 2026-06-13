# Convenience targets for local eval runs.
# CI runs the same scripts via .github/workflows/eval-smoke.yml.

.PHONY: eval-smoke eval-standard eval-release eval-check test

# Quick smoke — finishes in ~1 minute, mirrors CI gate.
eval-smoke:
	@mkdir -p docs/eval/results
	python3 scripts/eval/niah_scaling.py --N 500 --needles 30 --needle-mode semantic \
		--out docs/eval/results/niah_local_smoke.json
	python3 scripts/eval/miracl_ko.py --tier smoke \
		--out docs/eval/results/miracl_local_smoke.json
	python3 scripts/eval/check_regression.py \
		--result docs/eval/results/miracl_local_smoke.json \
		--baseline docs/eval/baseline_miracl_ko_smoke_2026-06-14.json \
		--policy scripts/eval/policy.yml

# Standard tier — 5~10 min, run weekly or on model/weights changes.
eval-standard:
	@mkdir -p docs/eval/results
	python3 scripts/eval/internal_bench.py --tier standard \
		--out docs/eval/results/internal_local_standard.json
	python3 scripts/eval/niah_scaling.py --N 200,1000,3000 --needles 50 --needle-mode semantic \
		--out docs/eval/results/niah_local_standard.json
	python3 scripts/eval/miracl_ko.py --tier standard \
		--out docs/eval/results/miracl_local_standard.json
	python3 scripts/eval/check_regression.py \
		--result docs/eval/results/miracl_local_standard.json \
		--baseline docs/eval/baseline_miracl_ko_standard_2026-06-14.json \
		--policy scripts/eval/policy.yml

# Release tier — heavy, run before tagging.
eval-release:
	@mkdir -p docs/eval/results
	python3 scripts/eval/internal_bench.py --tier release \
		--out docs/eval/results/internal_local_release.json
	python3 scripts/eval/niah_scaling.py --N 200,1000,3000,10000,30000 --needles 100 --needle-mode semantic \
		--out docs/eval/results/niah_local_release.json
	python3 scripts/eval/miracl_ko.py --tier release \
		--out docs/eval/results/miracl_local_release.json

# Re-check the most recent local results.
eval-check:
	python3 scripts/eval/check_regression.py \
		--result docs/eval/results/miracl_local_smoke.json \
		--baseline docs/eval/baseline_miracl_ko_smoke_2026-06-14.json \
		--policy scripts/eval/policy.yml

test:
	python3 -m unittest discover tests -q

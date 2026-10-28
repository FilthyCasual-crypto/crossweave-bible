# Crossweave - see CLAUDE.md before changing the data layer.
.DEFAULT_GOAL := help
PY := python3
PORT ?= 8000

help: ## list targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  %-10s %s\n", $$1, $$2}'

serve: ## static server on :$(PORT) - the app cannot run from file://
	@echo "http://localhost:$(PORT)"
	@cd app && $(PY) -m http.server $(PORT)

verify: ## data integrity + the ASCII rule (fast; run before every commit)
	@$(PY) scripts/verify.py

check: ## render every view headless, fail on console/page errors
	@node scripts/check.mjs
#  CW_CHROMIUM=/path/to/chromium make check   -> use a browser Playwright did not install
#  CW_BASE=http://host:port/index.html       -> check a deployed build instead of localhost

shots: ## same as check, plus 8 screenshots into .shots/
	@node scripts/check.mjs --shots && echo "screenshots in .shots/"

dev-deps: ## install the only dev dependency (Playwright, for check/shots)
	npm i -D playwright && npx playwright install chromium

sources: ## fetch the five upstream datasets into sources/ and check them against the baseline
	@mkdir -p sources
	@cd sources && \
	  curl -sSLO https://a.openbible.info/data/cross-references.zip && unzip -oq cross-references.zip && \
	  curl -sSL -o kjv.json https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json && \
	  curl -sSL -o bsb_bsb.txt https://bereanbible.com/bsb.txt && \
	  for f in ancient modern geometry; do \
	    curl -sSL -o $$f.jsonl https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/main/data/$$f.jsonl; \
	  done && \
	  curl -sSL -o ne_countries.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
	@$(PY) scripts/check_sources.py

data: ## full data rebuild, in dependency order (needs sources/ matching the baseline)
	@$(PY) scripts/check_sources.py
	$(PY) build/build.py
	$(PY) build/arcs.py
	$(PY) build/geo.py
	$(PY) build/spans.py
	$(PY) build/kingdoms.py
	$(PY) build/journeys.py
	@$(MAKE) --no-print-directory verify

clean: ## remove screenshots and caches
	rm -rf .shots __pycache__ build/__pycache__

.PHONY: help serve verify check shots dev-deps sources data clean

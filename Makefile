export MAYVARY_ORACLE ?= mayvary/mayvary@localhost:11521/FREEPDB1
export MAYVARY_POSTGRES ?= postgresql://mayvary:mayvary@localhost:15432/mayvary

.PHONY: up down demo fixes test

up:
	docker compose -f demo/compose.yaml up -d --wait

down:
	docker compose -f demo/compose.yaml down -v

# mayvary exits 1 when answers differ, which is the point of the demo.
demo: up
	uv run mayvary demo/cases.toml || test $$? -eq 1

fixes: up
	uv run mayvary demo/fixes.toml

test:
	uv run pytest

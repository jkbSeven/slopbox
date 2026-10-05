CODEDIRS := "src"

fmt:
	uv run ruff check --select I --fix {{CODEDIRS}}
	uv run ruff format {{CODEDIRS}}

fmt-check:
	uv run ruff format --check {{CODEDIRS}}

lint:
	uv run ruff check {{CODEDIRS}}

test:
    uv run pytest -v tests

ci: fmt-check lint test

polish: fmt lint

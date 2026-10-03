CODEDIRS := "src"

fmt:
	uv run ruff check --select I --fix {{CODEDIRS}}
	uv run ruff format {{CODEDIRS}}

lint:
	uv run ruff check {{CODEDIRS}}

test:
    uv run pytest -v tests

ci: fmt lint test

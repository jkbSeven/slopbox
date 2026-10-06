CODEDIRS := "src tests"

fmt:
	ruff check --select I --fix {{CODEDIRS}}
	ruff format {{CODEDIRS}}

fmt-check:
	ruff format --check {{CODEDIRS}}

lint:
	ruff check {{CODEDIRS}}

test:
    pytest -v tests

ci: fmt-check lint

CODEDIRS = src

all: fmt lint

fmt:
	uv run ruff check --select I --fix ${CODEDIRS}
	uv run ruff format ${CODEDIRS}

lint:
	uv run ruff check ${CODEDIRS}

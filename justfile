CODEDIRS := "src tests"

fmt:
	ruff check --select I --fix {{CODEDIRS}}
	ruff format {{CODEDIRS}}

fmt-check:
    ruff format --check {{CODEDIRS}}
    nix fmt -- --ci src/slopbox/nix

lint:
	ruff check {{CODEDIRS}}

test:
    pytest -v tests

ci: fmt-check lint

release-check:
    #!/bin/sh

    error() {
        printf '\x1b[1;31merror\x1b[0m: %s\n' "$@"
        exit 1
    }

    pyproject_version=$(grep "version" pyproject.toml | head -n 1 | sed -E 's/^version = "([[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+)"$/\1/') || error "version not found in pyproject.toml"
    const_module_version=$(grep "VERSION" src/slopbox/const.py | head -n 1 | sed -E 's/^VERSION = "([[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+)"$/\1/') || error "version not found in src/slopbox/const.py"
    changelog_version=$(grep --perl-regexp --only-matching "## \[\d+\.\d+\.\d+\]" CHANGELOG.md | head -n 1 | sed -E 's/^## \[([[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+)\]$/\1/') || error "version not found in CHANGELOG.md"

    printf 'Checking versions sync:\n'
    printf 'pyproject.toml: %s\n' "$pyproject_version"
    printf 'src/slopbox/const.py: %s\n' "$const_module_version"
    printf 'CHANGELOG.md: %s\n' "$changelog_version"

    [ "$pyproject_version" = "$const_module_version" ] || error "versions in pyproject.toml and src/slopbox/const.py differ"
    [ "$const_module_version" = "$changelog_version" ] || error "versions in CHANGELOG.md and src/slopbox/const.py differ"

    printf '\x1b[1;32mOK!\x1b[0m\n'

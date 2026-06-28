#!/bin/sh

error() {
    printf 'ERROR: %s\n' "$*" 1>&2
    exit 1
}

assert_installed() {
    if ! command -v $1 2>/dev/null 1>&2; then
        error "$1 is not installed but required"
    fi
}

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

OPTIONS:
    -h      print this help menu
    -l      print a list of available presets
    -p      specify a preset
EOF
}

if [ -L "$0" ]; then
    error 'Running this script through a symlink is not supported'
fi

SCRIPT_DIR=$(dirname $0)
EXEC_DIR=$(pwd)

# later we `cd` into the directory with compose
# so we don't need to pass the path to compose file
PRESETS_CLAUDE="docker compose run --rm -v $EXEC_DIR:/workspace -v claude_data:/home/agent/.claude -v ./.claude.json:/home/agent/.claude.json agent"


print_presets() {
    printf 'All commands are run in the context of the directory of this script: %s\n' "$SCRIPT_DIR"
    printf '> claude: %s\n' "$PRESETS_CLAUDE"
}


PRESET=
while getopts ":p:hl" opt; do
    case $opt in
        h) usage; exit 0 ;;
        l) print_presets; exit 0;;
        p) PRESET="$OPTARG" ;;
        *) printf 'Invalid option "%s"\n' "$opt"; usage; exit 1 ;;
    esac
done

if [ -z "$PRESET" ]; then
    error "You need to pass a preset with '-p <PRESET>'. List available presets with '-l'"
fi

CMD=
case $PRESET in
    claude) CMD=$PRESETS_CLAUDE;;
    *) error "Preset '$PRESET' is not available. List available presets with '-l'";;
esac


cd $SCRIPT_DIR || exit $?
docker compose up --wait proxy || exit $?

sh -c "$CMD"

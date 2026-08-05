from slopbox.const import Agent

__all__ = ["mounts", "proxy"]

mounts = {
    "workdir": ".:/workspace",
    "git-ro": ".git:/workspace/.git:ro",
    Agent.CLAUDE.value: [
        # FIXME: this assumes the home dir is `/home/agent`
        # ideally we would give user more control over this through some `home_dir` option in the confrig
        # would required changes in compose.yaml handling as well
        "~/.claude:/home/agent/.claude",
        "~/.claude.json:/home/agent/.claude.json",
    ],
}

proxy = {
    "python3": [
        "pypi.org",
        "*.pypi.org",
        "*.pythonhosted.org",
    ],
    "nodejs": [
        "npmjs.com",
        "*.npmjs.com",
        "npmjs.org",
        "registry.npmjs.org",
        "*.npmjs.org",
    ],
    "github": [
        "*.github.com",
        "github.com",
    ],
    Agent.CLAUDE.value: [
        "claude.com",
        "*.claude.com",
        "api.anthropic.com",
    ],
}

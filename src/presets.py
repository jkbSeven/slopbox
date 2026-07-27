from const import Agent

__all__ = [ "mounts", "proxy" ]

mounts = {
    "workdir": ".:/workspace",
    "git-ro": ".git:/workspace/.git:ro",
    Agent.CLAUDE.value: [
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
    ]
}

from enum import Enum


class Agent(Enum):
    CLAUDE = "claude-code"
    CODEX = "codex"
    OPENCODE = "opencode"


class SlopboxRuntime(Enum):
    CONTAINER = "container"
    VM = "vm"


UNFREE_AGENTS = (Agent.CLAUDE, Agent.CODEX)

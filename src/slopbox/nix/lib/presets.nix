{ lib }:
{
  mounts = {
    opencode = homeDir: [
      "~/.cache/opencode:${homeDir}/.cache/opencode"
      "~/.config/opencode:${homeDir}/.config/opencode"
      "~/.local/share/opencode:${homeDir}/.local/share/opencode"
      "~/.local/state/opencode:${homeDir}/.local/state/opencode"
    ];
    claude = homeDir: [
      "~/.claude:${homeDir}/.claude"
      "~/.claude.json:${homeDir}/.claude.json"
    ];
    codex = homeDir: "~/.codex:${homeDir}/.codex";
  };

  proxy = {
    opencode = [
      "opencode.ai"
      "*.opencode.ai"
    ];
    claude = [
      "anthropic.com"
      "*.anthropic.com"
      "claude.com"
      "*.claude.com"
    ];
    codex = [
      "openai.com"
      "*.openai.com"
      "chatgpt.com"
      "*.chatgpt.com"
    ];
    python = [
      "pypi.org"
      "*.pypi.org"
      "*.pythonhosted.org"
    ];
    github = [
      "github.com"
      "*.github.com"
    ];
    stackoverflow = [
      "stackoverflow.com"
      "*.stackoverflow.com"
    ];
  };
}

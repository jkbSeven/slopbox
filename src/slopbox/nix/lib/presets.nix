{ lib }:
{
  mounts = {
    opencode = homeDir: [
      { from = "~/.cache/opencode"; to = "${homeDir}/.cache/opencode"; }
      { from = "~/.config/opencode"; to = "${homeDir}/.config/opencode"; }
      { from = "~/.local/share/opencode"; to = "${homeDir}/.local/share/opencode"; }
      { from = "~/.local/state/opencode"; to = "${homeDir}/.local/state/opencode"; }
    ];
    claude = homeDir: [
      { from = "~/.claude"; to = "${homeDir}/.claude"; }
      { from = "~/.claude.json"; to = "${homeDir}/.claude.json"; type = "file"; autocreate.payload = "{}"; }
    ];
    codex = homeDir: { from = "~/.codex"; to = "${homeDir}/.codex"; };
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

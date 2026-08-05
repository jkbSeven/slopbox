# Slopbox
A secure-ish environment for running AI agents.

The goal of this project is to allow users to effortlessly setup
an isolated runtime (container or virtual machine) for the AI agent.

What you can expect:
* Principle of least privilege
   * include only the binaries that are neccessary for the agent to operate in your repo
   * restrict agent's network access through a customizable proxy
   * grant access to a subset of directories (no need to worry about leaking secrets or ssh keys)
* Batteries included but removable
   * slopbox comes in with presets for mounts and proxy rules for opencode and claude-code
   * configuration has sane defaults, which you can easily overwrite if needed
* Easy to use CLI

**DISCLAIMER**: this project is on a very early stage of development.
A lot of things will change and there will be a bunch of new features!

## Requirements
- Nix
- Docker
   - we assume rootless mode
   - guide for NixOS: https://wiki.nixos.org/wiki/Docker#Rootless_Docker
- Docker Compose

## Usage
1. Create a baseline config with `slopbox init`
   * this command will create a directory (default: `~/.config/slopbox`) with a baseline `config.json`
   * you can point slopbox to a custom config file through an option: `slopbox --config /path/to/config.json ...` or `SLOPBOX_CONFIG_FILE` env var
2. Adjust the baseline `config.json` file according to your needs
3. Inspect the configuration with `slopbox config`
   * you can see the final configuration, with resolved presets and profile references, by passing the `--resolved` option
4. Build a profile with `slopbox build`
   * this command uses the `default` profile by default, you can pass the `--profile <profile name>` option to change that
   * all profile builds are stored in `~/.local/state/slopbox` by default, you can change that by passing `--state-dir` option, or by setting the `SLOPBOX_STATE_DIR` env var
   * each profile has a dedicated directory named with a profile hash; you can list the hash for each profile with `slopbox config --hashes`
5. Run the environment with `slopbox run` (currently only containers are supported, VMs will be available in near future)
   * this command uses the `default` profile by default, you can pass the `--profile <profile name>` option to change that

You can use `-v` or `-vv` for more verbose logs, e.g. `slopbox -vv run`

## Docs
No documentation is available at this point. The schema in `docs/v1.jsonc` lists most of the available options.

## What's next
1. Support for running agents in virtual machines (microvm)
2. Support for passing a profile from a custom nix flake, so that users can easliy use their own overlays, etc.
3. Support for per-project slopbox extensions that will enable users to extend exisiting profiles with project-related dependencies, mounts, and proxy routes
4. Improve validation and error handling
5. Improve logging
6. Improve reproducibility

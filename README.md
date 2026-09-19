# Slopbox
A secure-ish environment for running AI agents.

The goal of this project is to allow users to effortlessly setup
an isolated runtime (container or virtual machine) for the AI agent.

What you can expect:
* Principle of least privilege
   * include only the binaries that are neccessary for the agent to operate in your repo
   * restrict agent's network access through a customizable proxy
   * grant access to a subset of directories
* Batteries included but removable

**DISCLAIMER**: this project is on a very early stage of development.
A lot of things will change and there will be a bunch of new features!

## Requirements
- Nix
- Docker
   - we assume rootless mode
   - guide for NixOS: https://wiki.nixos.org/wiki/Docker#Rootless_Docker
- Docker Compose

You can use `-v` or `-vv` for more verbose logs, e.g. `slopbox -vv run`

## Docs
No documentation is available at this point.

## What's next
1. Support for running agents in virtual machines (microvm)
2. Support for passing a profile from a custom nix flake, so that users can easliy use their own overlays, etc.
3. Support for per-project slopbox extensions that will enable users to extend exisiting profiles with project-related dependencies, mounts, and proxy routes
4. Improve validation and error handling
5. Improve logging
6. Improve reproducibility

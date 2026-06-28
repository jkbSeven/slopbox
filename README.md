# Slopbox
A secure-ish environment for running AI agents.

The goal is to give as little access as possible.
Agent container in docker compose has a read-only file system (except for custom volume mounts) and it can access the internet only through a restrictive proxy.

DISCLAIMER: This is not an out-of-the-box solution, you need to make adjustments for your setup.

## Requirements
- Nix
- Docker
   - scripts assume rootless mode
   - guide for NixOS: https://wiki.nixos.org/wiki/Docker#Rootless_Docker
- Docker Compose

## Usage

### Baseline claude-code setup
1. Clone the repo to a directory where you store projects and `cd` into it
2. Run `nix build .#slopbox && docker load < result`
3. Run `nix build .#slopbox-proxy && docker load < result`
4. Add an alias `alias slop="/path/to/repo/slop.sh"`
5. Run `slop -p claude` from the directory that you want to expose to claude.

### Customize
This flake exposes a `lib` output that contains the `lib.genSlopboxImage` helper function for building a docker image for the agent environment.
The function takes the following arguments:
- `imageName` (default: `slopbox`)
- `imageTag` (default: `latest`)
- `pkgs` (nixpkgs)
- `agentPkg` (e.g. opencode)
- `additionalPkgs` (optional)

Build your custom image:
1. Add the flake from this repo to your project's flake inputs
2. Define a Nix package (`outputs.packages`) that will build the custom image through `lib.genSlopboxImage`
3. Build the image and load it to docker `nix build .#<name-of-the-defined-package> && docker load < result`
4. Clone this repo to a directory where you store projects and `cd` into it
5. Run `nix build .#slopbox-proxy && docker load < result` (or define your own proxy setup)
6. Run `docker compose up --wait proxy`
7. Run `docker compose run --rm -v <volumes that you need and bind mount for project dir> agent`

## What's planned
- make slopbox easier to use
- investigate and fix issues with the current setup for [gVisor](https://github.com/google/gvisor) container runtime
- add setup for running agents in `microvm` so that slopbox is more secure (configured through the flake.nix)

# Slopbox
**A secure-ish environment for running AI agents.**

The goal of this project is to make it very easy to _set up
an isolated runtime_ (container or virtual machine) for an AI agent.

What you can expect:
* intuitive configuration with sane defaults
* principle of least privilege
   * include only the packages that are neccessary for the agent to operate
   * restrict agent's network access through a customizable proxy
   * grant access only to a subset of directories
* just works™

**DISCLAIMER**: this project is on a very early stage of development -- things will break, things will change.

## Requirements
- Nix
- Podman or Docker
   - rootless mode required
   - guide for docker on NixOS: https://wiki.nixos.org/wiki/Docker#Rootless_Docker

## Docs
No documentation is available at this point.

## What's next
See the list of [planned features](/issues?q=is%3Aissue+state%3Aopen+label%3Aenhancement+author%3AjkbSeven)

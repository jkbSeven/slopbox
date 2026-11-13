# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- templates for `slopbox init` command through `--template` option: `opencode`, `claude`, and `codex`
- `slopbox.nix` options `nixpkgs.config` and `nixpkgs.overlays` that are passed to nixpkgs during import
- if host directories or files used in bind mounts do not exist, they are can be created (see new type for `mounts` attribute)

### Changed
- `slopbox health` returns with exit code 1 when not healthy, previously the exit code was always 0
- type for `mounts` attribute in slopbox.nix profiles: used to be a string, now it's an attribute set

### Fixed
- on-exit container cleanup is more stable (previously, if the last user-invoked command exited with non-zero exit status, the cleanup would fail)

## [0.2.2] 2026-11-01

### Fixed
- updated version in pyproject.toml

## [0.2.1] 2026-11-01

### Fixed
- updated internal version variable :)

## [0.2.0] 2026-11-01

### Added
- slopbox as a flake package output -- slopbox can be installed with Nix directly

### Fixed
- configured agent workspace is now writeable (mounted as tmpfs unless user already configured bind mount)

## [0.1.0] 2026-10-31

### Added
- command `slopbox run` to run configured runtime
- command `slopbox profile` to print evaluated profile and build metadata
- command `slopbox build` to build containers for a profile
- option `--config` to select a different configuration source
- command `slopbox health` to check whether slopbox is operational (all dependencies are met)
- config schema for slopbox in `toml` format
- commands `slopbox config show` and `slopbox config edit` to display and edit slopbox config
- command `slopbox init` to create default environment config and lock external dependencies

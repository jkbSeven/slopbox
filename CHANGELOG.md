# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### ADDED
- option `--config` to select a different configuration source
- command `slopbox health` to check whether slopbox is operational (all dependencies are met)
- config schema for slopbox in `toml` format
- commands `slopbox config show` and `slopbox config edit` to display and edit slopbox config
- command `slopbox init` to create default environment config and lock external dependencies

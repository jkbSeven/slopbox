```sh
slopbox

slopbox --mount <host_path>:<guest_path>  # this would require a new project directory (new hash)

slopbox --proxy "git.my.com" --proxy "*.git.my.com"  # this would require a new project directory (new hash)

slopbox --config /path/to/config.json

slopbox --profile config-2

slopbox --set config.default.use_default_agent_mounts false

slopbox --ignore-project-flake

slopbox --no-proxy

slopbox --runtime vm|container
```

```sh
# dump default config
slopbox init

# check if docker, docker compose and nix are OK
slopbox health

# dump final config
slopbox config

# walk the user through config building process
slopbox explain

# build the current configuration but don't run anything (will be saved to .local/state/slopbox/<config-hash>)
slopbox build
```

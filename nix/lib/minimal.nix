{ config, lib, ... }:
{
  options.profiles = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule (
        { name, ... }: {
          config.env = {
            USER = config.profiles.${name}.user;
            HOME = config.profiles.${name}.homeDir;
          };
        }
      )
    );
  };
}

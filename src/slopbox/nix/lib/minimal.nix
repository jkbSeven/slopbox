{
  config,
  pkgs,
  lib,
  ...
}:
{
  options.profiles = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule (
        { name, ... }: {
          config.env = {
            USER = config.profiles.${name}.user;
            HOME = config.profiles.${name}.homeDir;
            SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
          };
        }
      )
    );
  };
}

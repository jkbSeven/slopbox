```
slopbox.lib.mkSlopboxProfile {
    pkgs = pkgs;
    runtimePkgs = [
        pkgs.python314
        pkgs.nodejs
    ];
    useBasePkgs = true;
    agentPkg = pkgs.claude-code;
}

|
|
V

{
    runtimePkgs = runtimePkgs ++ basePkgs (if useBasePkgs) ++ agentPkg;
    agent = nixpkgs.lib.getName agentPkg;
    container = nixpkgs.dockerTools.buildLayeredImage {
        name = "slopbox-<profile>"
        contents = runtimePkgs;
        config = {
            WorkingDir = "/workspace";
            Env = [
                "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
            ];
            Cmd = [ "${pkgs.bash}/bin/bash" ];
        }
    };
    microvm = (...);
}
```

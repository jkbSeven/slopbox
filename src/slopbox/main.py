import click

from slopbox.checks import (
    can_run,
    is_docker_available,
    is_nix_available,
    is_rootless_docker,
)

VERSION = "0.1.0"


class fmt:
    @staticmethod
    def red(msg: str):
        return click.style(msg, fg="red")

    @staticmethod
    def green(msg: str):
        return click.style(msg, fg="green")


def _err_if_unhealthy() -> None:
    if not can_run():
        raise click.ClickException(
            "slopbox health check failed, "
            "please run `slopbox health` and fix reported issues"
        )


@click.group()
def cli():
    """secure-ish environment for running AI agents"""


@cli.command()
def health():
    click.echo(f"version: {VERSION}")

    if is_nix_available():
        click.echo("nix: " + fmt.green("OK"))
    else:
        click.echo("nix: " + fmt.red("MISSING"))

    if not is_docker_available():
        click.echo("docker: " + fmt.red("MISSING"))
    else:
        click.echo("docker: " + fmt.green("INSTALLED"))
        click.echo(" - rootless: ", nl=False)

        rootless = is_rootless_docker()
        if rootless == 0:
            click.echo(fmt.red("NO"))
        elif rootless == 1:
            click.echo(fmt.green("YES"))
        else:
            click.echo(fmt.red("UNABLE TO CHECK"))


@cli.command()
def build():
    _err_if_unhealthy()
    click.echo("Hello, World!")


def main():
    cli()


if __name__ == "__main__":
    main()

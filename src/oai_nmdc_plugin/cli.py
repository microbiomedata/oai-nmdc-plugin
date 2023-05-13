"""Command line interface for oai-nmdc-plugin."""
import logging

import click

from oai_nmdc_plugin import __version__
from oai_nmdc_plugin.main import demo

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
@click.version_option(__version__)
def main(verbose: int, quiet: bool):
    """CLI for oai-nmdc-plugin.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


@main.command()
def run():
    """Run the oai-nmdc-plugin's demo command."""
    demo()


if __name__ == "__main__":
    main()

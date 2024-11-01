from pathlib import Path

import typer

import apod


def main(config: Path):
    apod.ApodBot.fromConfigFile(config).run()


typer.run(main)

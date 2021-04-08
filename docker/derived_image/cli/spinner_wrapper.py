from time import sleep
from typing import Any

import click
from halo import Halo


class SpinnerWrapper:
    def __init__(self, show_spinner: bool):
        self.spinner = Halo('', spinner='bouncingBall', animation='marquee', interval=220) if show_spinner else None
        self.in_progress = False

    def start(self, text: Any = None):
        if self.spinner:
            self.succeed()
            self.spinner.start(text)
            self.in_progress = True
            sleep(0.5)
        elif text:
            click.echo(text)

    def succeed(self, text: Any = None):
        if self.spinner and self.in_progress:
            self.spinner.succeed(text)
            sleep(0.5)
        self.in_progress = False

    def fail(self, text: Any = None):
        if self.spinner and self.in_progress:
            self.spinner.fail(text)
        self.in_progress = False

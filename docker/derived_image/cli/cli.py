import logging
import logging.handlers
import os
import sys
import traceback
import warnings

import click
from colorama import init

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '{}/../cloud_rail'.format(path))
sys.path.insert(0, '{}/'.format(path))
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.simplefilter("ignore", UserWarning)

import _version
from cloudrail_multi_command import CloudrailCLI
from utils.log_utils import LogUtils
from exit_codes import ExitCode
from cli_configuration import CliConfiguration, CliConfigurationKey


def _get_logger_level():
    config_log_level = CliConfiguration().get(CliConfigurationKey.LOG_LEVEL)
    if config_log_level:
        log_level = LogUtils.get_log_level_aliases()[config_log_level.upper()]
    else:
        log_level = logging.INFO
    return log_level


logger_file = os.getenv('LOGFILE', '/indeni/cli.log')
logger = logging.getLogger()
handler = logging.handlers.RotatingFileHandler(logger_file, maxBytes=10000000, backupCount=1)
handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
logger.addHandler(handler)
LogUtils.init_logger()
if os.path.isfile(logger_file):  # log already exists, roll over!
    handler.doRollover()


@click.command(cls=CloudrailCLI, help='Cloudrail CLI')
# TODO: get the right version for the right file
@click.version_option(_version.__version__)
def cli():
    """The root of commands."""


def safe_entry_point():
    try:
        init()
        cli()
    # in case dto is not align (bad class field or bad enum field) alert user to install new cli
    except (KeyError, ValueError) as ex:
        logging.exception(ex)
        click.echo('This version of Cloudrail CLI is too old. Please pull latest version and run again.')
        sys.exit(ExitCode.CLI_ERROR.value)
    except Exception as ex:
        msg = 'Error while running cli command'
        logging.exception(msg)
        traceback.print_exc()
        click.echo('\n{}. Error is:\n{}'.format(msg, str(ex)))
        sys.exit(ExitCode.CLI_ERROR.value)


if __name__ == '__main__':
    safe_entry_point()

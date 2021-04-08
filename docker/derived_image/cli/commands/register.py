import click

from api_client.cloudrail_api_client import CloudrailApiClient
from cli_configuration import CliConfiguration
from commands_utils import validate_input
from environment_context.common.input_validator import InputValidator
from service.cloudrail_cli_service import CloudrailCliService


def validate_email(unused_ctx, unused_param, value):
    return validate_input(value, InputValidator.validate_email)


def validate_first_name(unused_ctx, unused_param, value):
    return validate_input(value, InputValidator.validate_allowed_chars)


def validate_last_name(unused_ctx, unused_param, value):
    return validate_input(value, InputValidator.validate_allowed_chars)


@click.command(help='Create a new Cloudrail account')
@click.option('--email', '-e',
              prompt='Please enter the email address you would like to register with',
              help='The email address you would like to register with',
              type=click.STRING,
              callback=validate_email)
@click.option('--first-name', '-f',
              prompt='Please enter first name',
              help='First name',
              type=click.STRING,
              callback=validate_first_name)
@click.option('--last-name', '-l',
              prompt='Please enter last name',
              help='Last name',
              type=click.STRING,
              callback=validate_last_name)
@click.option('--password', '-p',
              prompt='The password you would like to use. The password should contain at least one uppercase character,'
                     ' one lowercase character, one numeric character, and be at least 8 characters in total',
              help='The password you would like to use. '
                   'The password should contain at least one uppercase character, '
                   'one lowercase character, one numeric character, and be at least 8 characters in total',
              hide_input=True,
              confirmation_prompt=True,
              type=click.STRING)
def register(email: str, password: str, first_name: str, last_name: str):
    '''
    register to cloudrail saas service using email and password.
    return back an API key. The API will be store in cloudrail local config file
    '''
    cloudrail_repository = CloudrailCliService(CloudrailApiClient(), CliConfiguration())
    result = cloudrail_repository.register(email, password, first_name, last_name)
    if result.success:
        click.echo(result.message)
        click.echo('Registration completed successfully. You can now begin to use the Cloudrail CLI tool.')
    else:
        click.echo(result.message)

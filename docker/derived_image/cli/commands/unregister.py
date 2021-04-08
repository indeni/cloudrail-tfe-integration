import click
from api_client.cloudrail_api_client import CloudrailApiClient
from service.cloudrail_cli_service import CloudrailCliService
from cli_configuration import CliConfiguration


@click.command(help='unregister (delete) cloudrail user')
@click.option('--email', '-e',
              prompt='Please enter the email address you would like to unregister (delete)',
              help='The email address you would like to unregister',
              type=click.STRING)
@click.option('--password', '-p',
              prompt='The password you would like to use',
              help='The password you would like to use',
              hide_input=True,
              confirmation_prompt=True,
              type=click.STRING)
def unregister(email: str, password: str):
    '''
    unregister user from cloudrail saas service.
    return back success/failure message
    '''
    cloudrail_repository = CloudrailCliService(CloudrailApiClient(), CliConfiguration())
    result = cloudrail_repository.unregister(email=email, password=password)
    if result.success:
        click.echo(result.message)
        click.echo(f"User={email} un registered successfully")
    else:
        click.echo(result.message)

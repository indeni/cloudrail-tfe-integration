from typing import List, Optional

import click
from click_aliases import ClickAliasedGroup
from colorama import Style, Fore
from tabulate import tabulate

from api.dtos.account_config_dto import AccountConfigDTO
from api_client.cloudrail_api_client import CloudrailApiClient
from cli_configuration import CliConfiguration
from commands_utils import exit_with_code, API_KEY_HELP_MESSAGE, validate_input, validate_cloud_account_input
from environment_context.common.input_validator import InputValidator
from exit_codes import ExitCode
from service.cloudrail_cli_service import CloudrailCliService


@click.group(name='cloud-account',
             short_help='Manage Cloudrail cloud accounts. Currently only AWS is supported.',
             help='Manage Cloudrail cloud accounts. Currently only AWS is supported.',
             cls=ClickAliasedGroup)
def cloud_account():
    pass


@cloud_account.command(name='add',
                       short_help='Add a cloud account to Cloudrail',
                       help='Add a cloud account to Cloudrail. Currently only AWS is supported.')
@click.option('--cloud-account-name', '-n',
              help='The name of your cloud account',
              type=click.STRING)
@click.option('--cloud-account-id', '-i',
              help='ID of AWS account to be added',
              type=click.STRING)
@click.option('--pull-interval',
              help='How often should Cloudrail scan your cloud account for changes',
              default=3600,
              type=click.INT)
@click.option('--api-key',
              help=API_KEY_HELP_MESSAGE,
              type=click.STRING)
def add_cloud_account(cloud_account_name: str, cloud_account_id: str, pull_interval: int, api_key):
    """
    Add could account to cloud rail, at this point we support only AWS.
    The process get the AWS account ID and generate a Terraform or cloud formation code
    for the user to run on his account that create a role for cloudrail to use later to collect
    his environment data.
    Once the role as been created the user need to provide the ARE and the external ID of this role
    """
    validate_input(cloud_account_id, InputValidator.validate_cloud_account_id,
                   error_message='The AWS Account ID should be 12 digits, without hyphens or other characters. Please try again')
    validate_input(cloud_account_name, InputValidator.validate_allowed_chars, error_message='Invalid cloud account name')
    cloudrail_service = CloudrailCliService(CloudrailApiClient(), CliConfiguration())
    if api_key:
        cloudrail_service.api_key = api_key
    result = cloudrail_service.add_cloud_account(cloud_account_name, cloud_account_id, pull_interval)

    if result.success:
        # now associate policies to this account, for now we have only one, internet connection
        click.echo(Fore.GREEN + '\nThank you, that worked.\n' + Style.RESET_ALL)
        click.echo('Please allow the Cloudrail Service some time to collect a snapshot of your live environment.')
    else:
        click.echo(result.message)
        exit_with_code(ExitCode.BACKEND_ERROR)


@cloud_account.command(aliases=['list', 'ls'],
                       short_help='List cloud accounts',
                       help='List cloud accounts that have already been added to Cloudrail')
@click.option("--api-key",
              help=API_KEY_HELP_MESSAGE,
              type=click.STRING)
def list_cloud_accounts(api_key):
    '''
    list all account that belongs to the user (same company id)
    The cli send the api key to the server which use it to select the relevant accounts
    The results is a table of all added accounts
    '''
    cloudrail_repository = CloudrailCliService(CloudrailApiClient(), CliConfiguration())
    if api_key:
        cloudrail_repository.api_key = api_key
    result = cloudrail_repository.list_cloud_accounts()
    if result.success:
        account_configs: List[AccountConfigDTO] = result.message
        if len(account_configs) > 0:
            values = [_convert_account_config_to_dict(account_config).values()
                      for account_config in account_configs]
            headers = list(_convert_account_config_to_dict(account_configs[0]).keys())
            click.echo(tabulate(values, headers=headers, tablefmt='plain'))
        else:
            click.echo('No accounts found.')
            click.echo('To add a cloud account use the \'cloud-account add\' command.')
    else:
        click.echo(result.message)


@cloud_account.command(aliases=['rm', 'remove'],
                       help='Remove a cloud account from Cloudrail')
@click.option('--cloud-account-id', '-i',
              help='Cloud Account ID of the cloud account that you wish to remove',
              type=click.STRING)
@click.option('--cloud-account-name', '-n',
              help='The name of the cloud account, as entered in Cloudrail',
              type=click.STRING)
@click.option("--api-key",
              help=API_KEY_HELP_MESSAGE,
              type=click.STRING)
def remove_cloud_account(cloud_account_id: Optional[str], cloud_account_name: Optional[str], api_key: str) -> None:
    '''
    remove cloud account by id.
    the CLI will send the API in the request so the server will
    validate that the user have permission to delete this account
    '''
    cloud_account_id = cloud_account_id or ''
    cloud_account_name = cloud_account_name or ''
    validate_cloud_account_input(cloud_account_id, cloud_account_name, allow_both_none=False)
    cloudrail_repository = CloudrailCliService(CloudrailApiClient(), CliConfiguration())
    if api_key:
        cloudrail_repository.api_key = api_key
    cloud_account_query = cloud_account_id or cloud_account_name
    result = cloudrail_repository.list_cloud_accounts(cloud_account_query)
    if result.success:
        account_configs: List[AccountConfigDTO] = result.message
        account_config_to_delete = next((ac for ac in account_configs
                                         if ac.cloud_account_id == cloud_account_id.strip()
                                         or ac.name == cloud_account_name.strip()), None)
        if account_config_to_delete:
            result = cloudrail_repository.remove_cloud_account(account_config_to_delete.id)
            if result.success:
                click.echo('Successfully removed account {0}'.format(cloud_account_id or cloud_account_name))
            else:
                click.echo(result.message)
                exit_with_code(ExitCode.BACKEND_ERROR)
        else:
            click.echo('Could not find match account config for cloud account {}'.format(cloud_account_id or cloud_account_name))
            exit_with_code(ExitCode.BACKEND_ERROR)
    else:
        click.echo(result.message)
        exit_with_code(ExitCode.BACKEND_ERROR)


def _convert_account_config_to_dict(account_config: AccountConfigDTO) -> dict:
    return {key: value for key, value in account_config.__dict__.items()
            if key in ['name', 'cloud_account_id', 'status', 'last_collected_at']}

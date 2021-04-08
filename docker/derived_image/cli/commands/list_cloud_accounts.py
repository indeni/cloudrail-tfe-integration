from typing import List

import click
from tabulate import tabulate

from api.dtos.account_config_dto import AccountConfigDTO
from api_client.cloudrail_api_client import CloudrailApiClient
from commands_utils import API_KEY_HELP_MESSAGE
from service.cloudrail_cli_service import CloudrailCliService
from cli_configuration import CliConfiguration


@click.command(short_help='List cloud accounts',
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
            click.echo('To add a cloud account use the add-cloud-account command.')
    else:
        click.echo(result.message)


def _convert_account_config_to_dict(account_config: AccountConfigDTO) -> dict:
    return {key: value for key, value in account_config.__dict__.items()
            if key in ['name', 'cloud_account_id', 'status', 'last_collected_at']}

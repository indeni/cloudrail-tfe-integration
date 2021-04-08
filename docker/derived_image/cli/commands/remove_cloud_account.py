from typing import List, Optional

import click

from api.dtos.account_config_dto import AccountConfigDTO
from api_client.cloudrail_api_client import CloudrailApiClient
from cli_configuration import CliConfiguration
from commands_utils import validate_cloud_account_input, API_KEY_HELP_MESSAGE, exit_with_code
from exit_codes import ExitCode
from service.cloudrail_cli_service import CloudrailCliService


@click.command(help='Remove a cloud account from Cloudrail')
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

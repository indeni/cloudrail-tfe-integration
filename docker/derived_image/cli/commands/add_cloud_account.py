import os
import re

import click
from colorama import Fore, Style
from halo import Halo

from api.dtos.customer_dto import CustomerDTO
from api.dtos.run_execution_dto import RunOriginDTO
from api_client.cloudrail_api_client import CloudrailApiClient
from cli_config import Configuration
from cli_configuration import CliConfiguration
from commands_utils import API_KEY_HELP_MESSAGE, exit_with_code
from exit_codes import ExitCode
from service.cloudrail_cli_service import CloudrailCliService
from utils.template_generator import generate_templates


class CustomerNotExistException(Exception):
    pass


global CLICK_GLOBAL_PATH


# pylint: disable=W0613,E0602
def assume_role_prompt(cloudrail_service, value) -> None:
    value = value.lower()
    customer = get_customer(cloudrail_service)
    indeni_account_id = Configuration.get('indeni_account_id')
    if value not in ['yes', 'y']:
        click.echo("You may create your own role for the Cloudrail Service to use to access your account. "
                   "Please make sure to follow these parameters:")
        click.echo(f"   - Role Name: {customer.role_name}")
        click.echo(f"   - External ID: {customer.external_id}")
        click.echo("   - Policies Required: ViewOnlyAccess, SecurityAudit")
        click.echo(f"   - AWS Account to Trust: {indeni_account_id}")
    else:
        ctf = generate_templates(customer,
                                 os.path.join(CLICK_GLOBAL_PATH, '../assume_role_template/cloudformation/cloudrail_viewonly_role.yaml.template'),
                                 indeni_account_id)
        tft = generate_templates(customer,
                                 os.path.join(CLICK_GLOBAL_PATH, '../assume_role_template/terraform/cloudrail_viewonly_role.tf.template'),
                                 indeni_account_id)

        click.echo('''\nTemplates generated. You can use either:
        * Cloudformation: ''' + ctf + '''
        * Terraform: ''' + tft)

    message = '\nOnce you have created the role, hit Enter to continue (or \'q\' to abort at this time and continue later)\n'
    value = input(message)
    if value in ('q', 'quit'):
        click.echo('Once you have the role ready rerun the add account command')
        exit_with_code(ExitCode.OK)


def get_customer(cloudrail_service) -> CustomerDTO:
    service_response = cloudrail_service.get_my_customer_data()
    if service_response.success:
        return service_response.message

    raise CustomerNotExistException('Failed to get customer information, try to register or login first')


def validate_account(ctx, param, value):
    aws_account_id_regex = r'^\d{12}$'
    if not re.match(aws_account_id_regex, value):
        click.echo('The AWS Account ID should be 12 digits, without hyphens or other characters. Please try again')
        value = click.prompt(param.prompt)
        return validate_account(ctx, param, value)
    return value


@click.command(short_help='Add a cloud account to Cloudrail',
               help='Add a cloud account to Cloudrail. Currently only AWS is supported.')
@click.option('--generate-assume-role-template',
              help='Set to YES to generate CloudFormation and Terraform templates for the role that is needed by Cloudrail.',
              prompt='Before adding a cloud account, please make sure to create a role for Cloudrail to assume in your account with '
                     'SecurityAudit and ViewOnlyAccess policies.\n\n'
                     'You can do this manually, or Cloudrail can generate a template for you to use '
                     '(both CloudFormation and Terraform). Would you like us to generate the cloudrail_viewonly_role template?',
              default='YES',
              show_default=False)
@click.option('--cloud-account-name', '-n',
              prompt='Enter the name of your cloud account',
              help='The name of your cloud account',
              type=click.STRING)
@click.option('--cloud-account-id', '-i',
              prompt='Enter the AWS Account ID of your cloud account',
              help='ID of AWS account to be added',
              type=click.STRING,
              callback=validate_account)
@click.option('--pull-interval',
              help='How often should Cloudrail scan your cloud account for changes',
              default=3600,
              type=click.INT)
@click.option('--api-key',
              help=API_KEY_HELP_MESSAGE,
              type=click.STRING)
@click.option('--origin',
              help='Set the cli run mode. Optional values are CI and Workstation',
              type=click.STRING,
              default=RunOriginDTO.WORKSTATION)
# pylint: disable=W0613
def add_cloud_account(generate_assume_role_template: bool, cloud_account_name: str, cloud_account_id: str, pull_interval: int, api_key, origin: str):
    """
    Add could account to cloud rail, at this point we support only AWS.
    The process get the AWS account ID and generate a Terraform or cloud formation code
    for the user to run on his account that create a role for cloudrail to use later to collect
    his environment data.
    Once the role as been created the user need to provide the ARE and the external ID of this role
    """

    cloudrail_service = CloudrailCliService(CloudrailApiClient(), CliConfiguration())
    if api_key:
        cloudrail_service.api_key = api_key
    assume_role_prompt(cloudrail_service, generate_assume_role_template)
    should_show_spinner = origin.lower() != RunOriginDTO.CI
    spinner = Halo(text='Adding account, testing that we can assume access account {} ({})'
                   .format(cloud_account_name, cloud_account_id), spinner='bouncingBall')
    if should_show_spinner:
        spinner.start()

    result = cloudrail_service.add_cloud_account(cloud_account_name, cloud_account_id, pull_interval)

    if result.success:
        spinner.succeed()
        # now associate policies to this account, for now we have only one, internet connection
        click.echo(Fore.GREEN + '\nThank you, that worked.\n' + Style.RESET_ALL)
        click.echo('Please allow the Cloudrail Service some time to collect a snapshot of your live environment.')
    else:
        spinner.stop()
        click.echo(result.message)
        exit_with_code(ExitCode.BACKEND_ERROR)

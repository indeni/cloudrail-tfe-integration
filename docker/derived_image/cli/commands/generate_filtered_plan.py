import logging
import os
import sys
import uuid

import click

from api.dtos.run_execution_dto import RunOriginDTO
from api_client.cloudrail_api_client import CloudrailApiClient
from api_client.external_api_client import ExternalApiClient
from cli_configuration import CliConfiguration
from commands_utils import validate_input_paths, echo_error, API_KEY_HELP_MESSAGE, exit_with_code, validate_origin, offer_to_upload_log_and_exit
from environment_context.common.terraform_service.terraform_context_service import TerraformContextService
from environment_context.common.terraform_service.terraform_plan_converter import TerraformPlanConverter
from error_messages import generate_convert_terraform_plan_to_json_failure_message, generate_process_plan_json_failure_message
from exit_codes import ExitCode
from service.cloudrail_cli_service import CloudrailCliService
from spinner_wrapper import SpinnerWrapper


@click.command(short_help='Generate the filtered Terraform plan to be used with \'run\' and save for analysis.'
                          ' This filtered plan can later be provided to \'run\'',
               help='Generate a filtered Terraform plan from a full Terraform plan. This context will not be uploaded '
                    'to the Cloudrail Service yet. You can review it before uploading, and then use the \'run\' command with the'
                    ' \'--filtered-plan\' parameter (instead of the \'--tf-plan\' parameter).')
@click.option("--tf-plan",
              help='The file path that was used in "terraform plan -out=file" call',
              prompt='Enter Terraform plan file path',
              type=click.STRING)
@click.option("--directory",
              help='The root directory of the .tf files - the same directory where you would run "terraform init". '
                   'If omitted, Cloudrail will attempt to determine it automatically by looking for the \'.terraform\' directory.',
              type=click.STRING)
@click.option('--origin',
              help='Where is Cloudrail being used - on a personal "workstation" or in a "ci" environment.',
              type=click.STRING,
              default=RunOriginDTO.WORKSTATION)
@click.option("--output-file",
              help='The file to save the results to. If left empty, results will appear in STDOUT.',
              type=click.STRING,
              default='')
@click.option("--api-key",
              help=API_KEY_HELP_MESSAGE,
              type=click.STRING)
@click.option('--notty',
              help='Use non-interactive mode',
              type=click.BOOL,
              is_flag=True,
              default=False)
@click.option('--upload-log',
              help='Upload log in case of failure',
              type=click.BOOL,
              is_flag=True,
              default=False)
@click.option('--no-upload-log',
              help='Do not upload logs in case of failure',
              type=click.BOOL,
              is_flag=True,
              default=False)
# pylint: disable=W0613
def generate_filtered_plan(directory: str, tf_plan: str, origin: str, output_file: str, api_key: str, notty: bool,
                           upload_log: bool, no_upload_log: bool):
    """
    Send Terraform out file to Cloudrail service for evaluation. We are getting back
    job_id and checking every X sec if the evaluation is done, once the evaluati
    """
    origin = validate_origin(origin)
    terraform_environment_context_service = TerraformContextService(TerraformPlanConverter())
    is_tty = origin != RunOriginDTO.CI and not notty and sys.stdout.isatty()
    plan_path, work_dir, unused_filtered_plan = validate_input_paths(tf_plan, directory, None, is_tty)

    cloudrail_repository = CloudrailCliService(CloudrailApiClient(), CliConfiguration())
    if api_key:
        cloudrail_repository.api_key = api_key

    spinner = SpinnerWrapper(show_spinner=is_tty)
    spinner.start('Starting...')
    customer_result = cloudrail_repository.get_my_customer_data()
    if not customer_result.success:
        spinner.fail()
        click.echo(customer_result.message)
        exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin, is_tty, None)
    customer_id = customer_result.message.id

    spinner.start('Re-running your Terraform plan through a customized \'terraform plan\' to generate needed context data...')
    service_result = terraform_environment_context_service.convert_plan_to_json(plan_path, work_dir)
    if service_result.success:
        spinner.succeed()
    else:
        # TODO submit failure
        spinner.fail()
        echo_error(generate_convert_terraform_plan_to_json_failure_message(service_result.error))
        exit_on_failure(cloudrail_repository, ExitCode.CLI_ERROR, upload_log, no_upload_log, origin, is_tty)

    spinner.start('Filtering and processing Terraform data...')

    supported_aws_services_result = cloudrail_repository.list_aws_supported_services()
    supported_checkov_services_result = cloudrail_repository.list_checkov_supported_services()

    if not supported_aws_services_result.success:
        spinner.fail()
        click.echo(supported_aws_services_result.message)
        exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin, is_tty)

    if not supported_checkov_services_result.success:
        spinner.fail()
        click.echo(supported_checkov_services_result.message)
        exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin, is_tty)

    supported_checkov_services = supported_checkov_services_result.message.supported_checkov_services
    checkov_results = terraform_environment_context_service.run_checkov_checks(work_dir, supported_checkov_services)

    if not checkov_results.success:
        echo_error(checkov_results.error)
        exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin, is_tty)

    service_result = terraform_environment_context_service.process_json_result(service_result.result,
                                                                               supported_aws_services_result.message.supported_aws_services,
                                                                               checkov_results.result,
                                                                               customer_id,
                                                                               ExternalApiClient.get_cli_handshake_version())
    if service_result.success:
        spinner.succeed()
        spinner.start('Obfuscating IP addresses...')
        spinner.succeed()
    else:
        spinner.fail()
        echo_error(generate_process_plan_json_failure_message(service_result.error))
        exit_on_failure(cloudrail_repository, ExitCode.CLI_ERROR, upload_log, no_upload_log, origin, is_tty)

    if output_file:
        spinner.start('Saving results to file {}'.format(output_file))
        _save_result_to_file(service_result.result, output_file)
        spinner.succeed()
    else:
        click.echo(service_result.result)
        exit_with_code(ExitCode.OK)


def _save_result_to_file(context: str, output_file: str) -> None:
    try:
        full_path = os.path.join(os.getcwd(), output_file)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as writer:
            writer.write(context)
    except Exception:
        logging.exception('could not write result to file')
        click.echo('failed to write result to file. check folder permission and access.')
        exit_with_code(ExitCode.INVALID_INPUT)


def exit_on_failure(cloudrail_repository: CloudrailCliService,
                    exit_code: ExitCode,
                    upload_logs: bool,
                    no_upload_log: bool,
                    origin: RunOriginDTO,
                    is_tty: bool,
                    job_id: str = None):
    if not job_id:
        job_id = str(uuid.uuid4())
    offer_to_upload_log_and_exit(cloudrail_repository, exit_code, upload_logs, no_upload_log, origin,
                                 is_tty, job_id, 'generate_filtered_plan')

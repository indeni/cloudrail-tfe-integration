import os
import sys
from typing import Optional

import click
from colorama import Fore

from api.dtos.run_execution_dto import RunOriginDTO
from environment_context.common.input_validator import ValidationException
from error_messages import SERVICE_ERROR_MESSAGE, SERVICE_ERROR_NO_FAIL_ON_SERVICE_ERROR_MESSAGE, OFFER_TO_UPLOAD_LOGS_WORKSTATION_MESSAGE, \
    OFFER_TO_UPLOAD_LOGS_CI_MESSAGE
from exit_codes import ExitCode
from service.cloudrail_cli_service import CloudrailCliService

TF_FOLDER_MISSING_TERRAFORM_FOLDER = 'Please make sure the directory you provide "{}" has the ".terraform" directory directly under it.'


def validate_origin(origin: str, no_fail_on_service_error: Optional[bool] = None) -> RunOriginDTO:
    optional_origins = [run_origin.value for run_origin in RunOriginDTO]
    if origin not in optional_origins:
        echo_error('Optional origin values are {}. Please try again'.format(optional_origins))
        exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)
    return RunOriginDTO(origin)


def validate_input(value: str, validate_method, error_message: str = None) -> str:
    try:
        if error_message:
            validate_method(value, error_message=error_message)
        else:
            validate_method(value)
    except ValidationException as ex:
        echo_error(str(ex))
        exit_with_code(ExitCode.INVALID_INPUT)
    return value


def validate_cloud_account_input(cloud_account_id: Optional[str],
                                 cloud_account_name: Optional[str],
                                 allow_both_none: bool):
    if not cloud_account_name and not cloud_account_id and not allow_both_none:
        echo_error('Please provide \'-cloud-account-id\' or \'-cloud-account-name\'.')
        exit_with_code(ExitCode.INVALID_INPUT)
    if cloud_account_name and cloud_account_id:
        echo_error('Please provide only \'-cloud-account-id\' or \'-cloud-account-name\'.')
        exit_with_code(ExitCode.INVALID_INPUT)


def validate_input_paths(plan_path: str,
                         work_dir: str,
                         filtered_plan: Optional[str],
                         allow_prompt: bool):
    if not filtered_plan:
        if not plan_path:
            if allow_prompt:
                plan_path = click.prompt('Enter Terraform plan file path', default='')
            else:
                echo_error('Please provide the \'-p\' flag, pointing to the Terraform plan file path you wish to evaluate.')
                exit_with_code(ExitCode.INVALID_INPUT)
        plan_path = plan_path.strip()
        abs_plan_path = os.path.abspath(plan_path)
        if not os.path.isfile(abs_plan_path):
            echo_error(f'The path you have provided "{plan_path}" does not point to a specific file.'
                       '\nPlease provide the path directly to the plan file you wish to use Cloudrail with.')
            exit_with_code(ExitCode.INVALID_INPUT)
        work_dir = _try_to_find_work_dir(work_dir, plan_path)
        if work_dir is None:
            if allow_prompt:
                work_dir = click.prompt('Enter the directory where you ran Terraform init (use \'-d\' to skip this)',
                                        default=os.path.dirname(plan_path))
            else:
                echo_error('Please provide the \'-d\' flag, pointing to the directory where you ran Terraform init.')
                exit_with_code(ExitCode.INVALID_INPUT)
        work_dir = work_dir.strip()
        abs_work_dir = os.path.abspath(work_dir)
        if not os.path.isdir(abs_work_dir):
            echo_error('"{}" is not a directory or does not exist.'
                       '\nPlease review and provide the path to the root of the Terraform files for which '
                       'you created the plan.'.format(work_dir))
            exit_with_code(ExitCode.INVALID_INPUT)
        terraform_path = os.path.join(abs_work_dir, '.terraform')
        if not os.path.isdir(terraform_path):
            echo_error(TF_FOLDER_MISSING_TERRAFORM_FOLDER.format(work_dir))
            exit_with_code(ExitCode.INVALID_INPUT)
        work_dir = abs_work_dir
        plan_path = abs_plan_path
    else:
        filtered_plan = filtered_plan.strip()
        abs_filtered_plan = os.path.abspath(filtered_plan)
        if not os.path.isfile(abs_filtered_plan):
            echo_error(f'The path you have provided "{filtered_plan}" does not point to a specific file.'
                       ' Please provide the path directly to the filtered plan.')
            exit_with_code(ExitCode.INVALID_INPUT)
        filtered_plan = abs_filtered_plan
    return plan_path, work_dir, filtered_plan


def _is_terraform_folder_exists(folder: str) -> bool:
    terraform_path = os.path.join(os.path.abspath(folder), '.terraform')
    return os.path.isdir(terraform_path)


def _try_to_find_work_dir(work_dir: str, plan_path: str) -> Optional[str]:
    if work_dir is not None:
        return work_dir
    plan_path_dir = os.path.dirname(plan_path)
    if _is_terraform_folder_exists(os.path.abspath(plan_path_dir)):
        return plan_path_dir
    current_dir = os.getcwd()
    if _is_terraform_folder_exists(current_dir):
        return plan_path_dir
    return None


def echo_error(message: str):
    click.echo(Fore.RED + '\n' + message)


API_KEY_HELP_MESSAGE = 'The API key to use to communicate with the Cloudrail Service. ' \
                       'If omitted, a CLOUDRAIL_API_KEY environment variable can be used. ' \
                       'Otherwise, the configuration saved to /indeni on the container will be used.'


def safe_invoke(func, *arg):
    try:
        return func(*arg)
    except ValidationException as ex:
        echo_error(str(ex))
        exit_with_code(ExitCode.INVALID_INPUT)
    except Exception as ex:
        echo_error(str(ex))
        exit_with_code(ExitCode.CLI_ERROR)


def exit_with_code(code: ExitCode, no_fail_on_service_error: Optional[bool] = None):
    if no_fail_on_service_error is None:
        sys.exit(code.value)
    if code in [ExitCode.BACKEND_ERROR,
                ExitCode.TIMEOUT,
                ExitCode.CLI_ERROR,
                ExitCode.CONTEXT_ERROR]:
        if no_fail_on_service_error:
            click.echo(SERVICE_ERROR_MESSAGE)
            sys.exit(ExitCode.OK.value)
        else:
            click.echo(SERVICE_ERROR_NO_FAIL_ON_SERVICE_ERROR_MESSAGE.format(code.value))
            sys.exit(code.value)
    else:
        sys.exit(code.value)


def prompt_choice(text: str, options: list):
    value = click.prompt(text, type=str).lower()
    while value not in options:
        value = click.prompt('Please select one of the options ({})'.format('/'.join(options).upper()), type=str)
    return value


def read_log_file():
    logger_file = os.getenv('LOGFILE', '/indeni/cli.log')
    with open(logger_file, 'r') as file:
        log = file.read()
        return log


def upload_log(log: str, job_id: str, command: str, cloudrail_repository: CloudrailCliService):
    click.echo('Uploading cli.log...')
    cloudrail_repository.upload_log(log, job_id, command)
    click.echo('Upload completed. A member of our support team has been notified.')


def offer_to_upload_log(command: str, job_id: str, origin: RunOriginDTO, is_tty: bool, upload_logs: bool, no_upload_logs: bool,
                        cloudrail_repository: CloudrailCliService):
    if no_upload_logs:
        return
    log = read_log_file()
    if upload_logs:
        cloudrail_repository.upload_log(log, job_id, command)
        click.echo('\nWe apologize as this error is unexpected. A log has been uploaded and a member of our support team has been notified.')
        return
    if origin == RunOriginDTO.WORKSTATION and is_tty:
        value = prompt_choice(OFFER_TO_UPLOAD_LOGS_WORKSTATION_MESSAGE, ['r', 'u', 'n'])
        if value == 'r':
            click.echo(log)
            approved = click.confirm('OK to upload the log?')
            if approved:
                upload_log(log, job_id, command, cloudrail_repository)
            else:
                click.echo('Skipping log upload.')
        if value == 'u':
            upload_log(log, job_id, command, cloudrail_repository)
        if value == 'n':
            click.echo('Skipping log upload.')
    else:
        click.echo(OFFER_TO_UPLOAD_LOGS_CI_MESSAGE)


def offer_to_upload_log_and_exit(cloudrail_repository: CloudrailCliService,
                                 exit_code: ExitCode,
                                 upload_logs: bool,
                                 skip_upload_logs: bool,
                                 origin: RunOriginDTO,
                                 is_tty: bool,
                                 job_id: str,
                                 command: str,
                                 no_fail_on_service_error: bool = None):
    offer_to_upload_log(command, job_id, origin, is_tty, upload_logs, skip_upload_logs, cloudrail_repository)
    exit_with_code(exit_code, no_fail_on_service_error)

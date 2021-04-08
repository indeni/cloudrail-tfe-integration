import os
import re
import sys
import uuid
from time import sleep, time
from typing import List, Optional

import click
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.data import JsonLexer
from pygments.styles.monokai import MonokaiStyle

from api.dtos.account_config_dto import AccountStatusDTO, AccountConfigDTO
from api.dtos.policy_dto import PolicyDTO
from api.dtos.rule_result_dto import RuleResultDTO, RuleResultStatusDTO
from api.dtos.run_execution_dto import AssessmentJobDTO, RunStatusDTO, StepFunctionStepDTO, RunTypeDTO, RunOriginDTO
from api_client.cloudrail_api_client import CloudrailApiClient
from api_client.external_api_client import ExternalApiClient
from cli_configuration import CliConfiguration
from commands_utils import validate_input_paths, echo_error, API_KEY_HELP_MESSAGE, exit_with_code, validate_origin, validate_cloud_account_input, \
    offer_to_upload_log_and_exit
from environment_context.common.terraform_service.terraform_context_service import TerraformContextService
from environment_context.common.terraform_service.terraform_plan_converter import TerraformPlanConverter
from error_messages import generate_convert_terraform_plan_to_json_failure_message, \
    generate_process_plan_json_failure_message, generate_simple_message, generate_failure_message
from exit_codes import ExitCode
from result_formatter.json_formatter import JsonFormatter
from result_formatter.json_gitlab_sast_formatter import JsonGitLabSastFormatter
from result_formatter.junit_formatter import JunitFormatter
from result_formatter.sarif_formatter import SarifFormatter
from result_formatter.text_formatter import TextFormatter
from service.cloudrail_cli_service import CloudrailCliService
from spinner_wrapper import SpinnerWrapper


def validate_account(cloud_account_id: str, no_fail_on_service_error: bool) -> str:
    aws_account_id_regex = r'^\d{12}$'
    if cloud_account_id and not re.match(aws_account_id_regex, cloud_account_id):
        echo_error('The AWS Account ID should be 12 digits, without hyphens or other characters. Please try again')
        exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)
    return cloud_account_id


def validate_build_link(build_link: str, origin: RunOriginDTO, no_fail_on_service_error: bool):
    if origin == RunOriginDTO.CI and not build_link:
        echo_error('You\'ve set --origin to \'ci\', please also supply \'--build-link\'.')
        exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)
    return build_link


@click.command(short_help='Evaluate security risks in IaC, produce Assessment',
               help='Evaluate the security of the environment using Terraform plan file to '
                    'anticipate what type of security risk will be expose after applying the Terraform plan')
@click.option('--tf-plan', '-p',
              help='The file path that was used in "terraform plan -out=file" call',
              default='',
              type=click.STRING)
@click.option("--directory", '-d',
              help='The root directory of the .tf files - the same directory where you would run "terraform init". '
                   'If omitted, Cloudrail will attempt to determine it automatically by looking for the \'.terraform\' directory.',
              type=click.STRING)
@click.option("--filtered-plan",
              help='The path to the filtered Terraform plan output file resulting from using generate-filtered-plan',
              default='',
              type=click.STRING)
@click.option("--api-key",
              help=API_KEY_HELP_MESSAGE,
              type=click.STRING)
@click.option('--output-format', '-o',
              help='The output format. Options are text, json, junit, json-gitlab-sast, sarif. Default is "text"',
              default='text',
              type=click.STRING)  # TODO: use enum: https://github.com/pallets/click/issues/605
@click.option('--output-file', '-f',
              help='The file to save the results to. If left empty, results will appear in STDOUT.',
              type=click.STRING,
              default='')
@click.option('--cloud-account-id', '-i',
              help='The AWS Account ID of your cloud account',
              type=click.STRING)
@click.option('--cloud-account-name', '-i',
              help='The name of the cloud account, as entered in Cloudrail',
              type=click.STRING)
@click.option('--origin',
              help='Where is Cloudrail being used - on a personal "workstation" or in a "ci" environment.',
              type=click.STRING,
              default=RunOriginDTO.WORKSTATION)
@click.option('--build-link',
              help='When using Cloudrail within CI ("ci" in origin), '
                   'supply a link directly to the build. Cloudrail does not access this link, but shows it to the user.',
              type=click.STRING)
@click.option('--execution-source-identifier',
              help='An identifier that will help users understand the context of execution for this run. '
                   'For example, you can enter "Build #81 of myrepo/branch_name".',
              type=click.STRING)
@click.option("--auto-approve",
              help='Should we auto approve sending the filtered plan to the Cloudrail Service',
              is_flag=True)
@click.option("--refresh-cloud-account-snapshot",
              help='Forces a refresh of the cloud account snapshot. '
                   'This may add several minutes to the entire time it takes to execute a run, '
                   'depending on the size and complexity of the cloud account.',
              is_flag=True)
@click.option('--junit-package-name-prefix',
              help='When producing results in a JUnit format, Cloudrail will use a prefix for all package names. '
                   'Use this parameter to change the default prefix from ‘cloudrail.’ to something else.',
              type=click.STRING,
              default='cloudrail.')
@click.option('--verbose', '-v', '--show-warnings',
              help='By default, Cloudrail will not show WARNINGs. With this flag, they will be included in the output.',
              is_flag=True,
              default=False)
@click.option('--notty',
              help='Use non-interactive mode',
              is_flag=True,
              default=False)
@click.option('--no-fail-on-service-error',
              help='By default, Cloudrail will fail with exit code 4 on context errors. With this flag,'
                   ' the exit code will be 0.',
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
def run(api_key: str,
        directory: str,
        tf_plan: str,
        output_format: str,
        cloud_account_id: str,
        cloud_account_name: str,
        output_file: str,
        origin: str,
        build_link: str,
        execution_source_identifier: str,
        filtered_plan: str,
        auto_approve: bool,
        refresh_cloud_account_snapshot: bool,
        junit_package_name_prefix: str,
        verbose: bool,
        notty: bool,
        no_fail_on_service_error: bool,
        upload_log: bool,
        no_upload_log: bool):
    """
    Send Terraform out file to Cloudrail service for evaluation. We are getting back
    job_id and checking every X sec if the evaluation is done, once the evaluati
    """
    cloud_account_id = validate_account(cloud_account_id, no_fail_on_service_error)
    origin = validate_origin(origin, no_fail_on_service_error)
    build_link = validate_build_link(build_link, origin, no_fail_on_service_error)
    _show_origin_warning_message(origin)
    api_client = CloudrailApiClient()
    cloudrail_repository = CloudrailCliService(api_client, CliConfiguration())
    terraform_environment_context_service = TerraformContextService(TerraformPlanConverter())
    if api_key:
        cloudrail_repository.api_key = api_key
    validate_cloud_account_input(cloud_account_id, cloud_account_name, allow_both_none=True)
    account_config = _get_account_config(cloudrail_repository, cloud_account_id, cloud_account_name, no_fail_on_service_error)
    account_policies = _get_account_policies(cloudrail_repository, account_config, no_fail_on_service_error)
    is_tty = origin != RunOriginDTO.CI and not notty and sys.stdout.isatty()
    plan_path, work_dir, filtered_plan_path = validate_input_paths(tf_plan, directory, filtered_plan, is_tty)
    show_spinner = is_tty

    spinner = SpinnerWrapper(show_spinner=show_spinner)
    spinner.start('Preparing a filtered Terraform plan locally before uploading to Cloudrail Service...')
    result = cloudrail_repository.run(account_config.id,
                                      origin,
                                      build_link,
                                      execution_source_identifier,
                                      refresh_cloud_account_snapshot)
    if result.success:
        run_execution: AssessmentJobDTO = result.message
        job_id = run_execution.id
        account_config = _get_cloud_account(cloudrail_repository, result.message.account_config_id, no_fail_on_service_error)
        run_status = RunStatusDTO.RUNNING
        last_step = None
        if not filtered_plan:
            spinner.start('Re-running your Terraform plan through a customized \'terraform plan\' to generate needed context data...')
            service_result = terraform_environment_context_service.convert_plan_to_json(plan_path, work_dir)
            if service_result.success:
                spinner.succeed()
            else:
                cloudrail_repository.submit_failure(service_result.error, job_id)
                spinner.fail()
                echo_error(generate_convert_terraform_plan_to_json_failure_message(service_result.error, job_id))
                exit_on_failure(cloudrail_repository, ExitCode.CLI_ERROR, upload_log, no_upload_log, origin,
                                is_tty, job_id, no_fail_on_service_error)

            spinner.start('Filtering and processing Terraform data...')
            supported_aws_services_result = cloudrail_repository.list_aws_supported_services()
            supported_checkov_services_result = cloudrail_repository.list_checkov_supported_services()

            if not supported_aws_services_result.success:
                echo_error(supported_aws_services_result.message)
                exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin,
                                is_tty, job_id, no_fail_on_service_error)

            if not supported_checkov_services_result.success:
                echo_error(supported_checkov_services_result.message)
                exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin,
                                is_tty, job_id, no_fail_on_service_error)

            supported_checkov_services = supported_checkov_services_result.message.supported_checkov_services
            checkov_results = terraform_environment_context_service.run_checkov_checks(work_dir, supported_checkov_services)

            if not checkov_results.success:
                echo_error(checkov_results.error)
                exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin,
                                is_tty, job_id, no_fail_on_service_error)

            service_result = terraform_environment_context_service.process_json_result(service_result.result,
                                                                                       supported_aws_services_result.message.supported_aws_services,
                                                                                       checkov_results.result,
                                                                                       account_config.customer_id,
                                                                                       ExternalApiClient.get_cli_handshake_version())

            if service_result.success:
                spinner.succeed()
                spinner.start('Obfuscating IP addresses...')
                spinner.succeed()
            else:
                cloudrail_repository.submit_failure(service_result.error, job_id)
                spinner.fail()
                echo_error(generate_process_plan_json_failure_message(service_result.error, job_id))
                exit_on_failure(cloudrail_repository, ExitCode.CLI_ERROR, upload_log, no_upload_log, origin, is_tty,
                                job_id, no_fail_on_service_error)

            if not auto_approve:
                if not is_tty:
                    echo_error('You have chosen to do a full run without interactive login. '
                               'This means Cloudrail CLI cannot show you the filtered plan prior to uploading to the Cloudrail Service. '
                               'In such a case you can either:'
                               '\n1. Execute \'cloudrail generate-filtered-plan\' '
                               'first, then provide the file to \'cloudrail run --filtered-plan\'.'
                               '\n2. Re-run \'cloudrail run\' with \'--auto-approve\', '
                               'indicating you are approving the upload of the filtered plan to Cloudrail Service.')
                    exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)
                click.echo(highlight(service_result.result, JsonLexer(), Terminal256Formatter(style=MonokaiStyle)))
                if checkov_results.result:
                    click.echo('For some non-context-aware rules, '
                               'Cloudrail utilized the Checkov engine and found a few violations.'
                               '\nSuch violations will be marked with the \'CKV_*\' rule ID.\n')
                approved = click.confirm('OK to upload this Terraform data to Cloudrail'
                                         ' (use \'--auto-approve\' to skip this in the future)?', default=True)
                if not approved:
                    cloudrail_repository.submit_failure('terraform data not approved for upload', job_id)
                    echo_error('Upload not approved. Aborting.')
                    exit_with_code(ExitCode.USER_TERMINATION, no_fail_on_service_error)

            spinner.start('Submitting Terraform data to the Cloudrail Service...')
            service_result = cloudrail_repository.submit_terraform_context(service_result.result, job_id)
            if not service_result.success:
                spinner.fail()
                echo_error(generate_simple_message(service_result.message, job_id))
                exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin, is_tty,
                                job_id, no_fail_on_service_error)

        else:
            service_result = terraform_environment_context_service.read_terraform_output_file(filtered_plan_path)
            if service_result.success:
                spinner.start('Submitting Terraform data to the Cloudrail Service...')
                service_result = cloudrail_repository.submit_terraform_context(service_result.result, job_id)
                if not service_result.success:
                    spinner.fail()
                    echo_error(generate_simple_message(service_result.message, job_id))
                    exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin,
                                    is_tty, job_id, no_fail_on_service_error)
            else:
                echo_error(generate_simple_message('Error while reading json file. This is probably due to an '
                                                   'outdated Terraform show output generated by Cloudrail CLI container.'
                                                   '\nPlease pull the latest version of this container and use \'generated-filtered-plan\' '
                                                   'to regenerate the file.', job_id))
                exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)

        spinner.start('Your job id is: {0}'.format(job_id))
        _show_account_collect_message(refresh_cloud_account_snapshot, run_execution, account_config, spinner)
        spinner.succeed()
        result_timeout_sec: int = 600
        end_time: float = time() + result_timeout_sec
        while run_status == RunStatusDTO.RUNNING and end_time >= time():
            sleep(2)
            service_result = cloudrail_repository.get_run_status(job_id)
            if not service_result.success:
                echo_error(generate_simple_message('Error while waiting for analysis: {0}'.format(service_result.message), job_id))
                exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin, is_tty,
                                job_id, no_fail_on_service_error)
            run_execution: AssessmentJobDTO = service_result.message
            messages = _get_progress_messages(last_step, service_result.message.last_step)
            for msg in messages:
                spinner.start(msg)
                sleep(1)
            last_step = run_execution.last_step
            run_status = run_execution.run_status
            if end_time < time():
                echo_error(generate_simple_message('Timeout while waiting for assessment to be completed. Please try again.'
                                                   '\nIf the issue persists, please contact us using the details provided below.', job_id))
                exit_with_code(ExitCode.TIMEOUT, no_fail_on_service_error)

        if run_status == RunStatusDTO.SUCCESS:
            spinner.start('Assessment complete, fetching results...')
            result = cloudrail_repository.get_run_results(job_id)

            if result.success:
                spinner.succeed()
                rule_results: List[RuleResultDTO] = result.message
                stylize = output_file == ''
                censored_api_key = 'XXXXX' + cloudrail_repository.api_key[-4:]
                formatter = _get_formatter(output_format, censored_api_key, work_dir, plan_path, junit_package_name_prefix, stylize, verbose)
                format_result, notices = formatter(rule_results, service_result.message, account_policies)
                if output_file:
                    _save_result_to_file(format_result, output_file)
                else:
                    click.echo(format_result)

                if notices:
                    click.echo(notices)
                ui_url = f'{api_client.get_api_base_url()}/environments/assessments/{job_id}'.replace('api', 'web')
                click.echo(f'To view this assessment in the Cloudrail Web UI, '
                           f'go to {ui_url}')
                _send_exit_code(rule_results, no_fail_on_service_error)
        else:
            spinner.fail()
            echo_error(generate_failure_message(last_step, run_execution.error_message, job_id, account_config))
            exit_on_failure(cloudrail_repository, _process_failure_to_exit_code(service_result.message), upload_log, no_upload_log, origin,
                            is_tty, job_id, no_fail_on_service_error)
    else:
        echo_error(generate_simple_message(result.message))
        exit_on_failure(cloudrail_repository, ExitCode.BACKEND_ERROR, upload_log, no_upload_log, origin, is_tty, None,
                        no_fail_on_service_error)


def _send_exit_code(rule_results: List[RuleResultDTO], no_fail_on_service_error):
    for rule_result in rule_results:
        if rule_result.status == RuleResultStatusDTO.FAILED \
                and rule_result.is_mandate:
            exit_with_code(ExitCode.MANDATORY_RULES_FAILED, no_fail_on_service_error)
    exit_with_code(ExitCode.OK, no_fail_on_service_error)


def _get_formatter(output_format: str, api_key: str, directory: str, plan_path: str, junit_package_name_prefix: str, stylize: bool, verbose: bool):
    if output_format == 'junit':
        click.echo('IMPORTANT: When using the JUnit format output, Cloudrail CLI will only include rules that are set to ‘mandate’. '
                   'If a violation is found with such rules, a test failure will be logged in the JUnit output. '
                   'Rules that are set to ‘advise’ will not be included in the JUnit output, and can be viewed in the Cloudrail web user interface.')
        return JunitFormatter(api_key, directory, plan_path, junit_package_name_prefix).format
    if output_format == 'json':
        return JsonFormatter(verbose).format
    if output_format == 'json-gitlab-sast':
        return JsonGitLabSastFormatter(verbose).format
    if output_format == 'sarif':
        return SarifFormatter(verbose).format
    return TextFormatter(stylize, verbose).format


def _get_cloud_account(cloudrail_repository: CloudrailCliService,
                       account_config_id: str,
                       no_fail_on_service_error: bool) -> AccountConfigDTO:
    result = cloudrail_repository.list_cloud_accounts()
    if result.success:
        account_configs: List[AccountConfigDTO] = result.message
        for account_config in account_configs:
            if account_config.id == account_config_id:
                return account_config
        echo_error('Error finding account config id {}'.format(account_config_id))
        return exit_with_code(ExitCode.BACKEND_ERROR, no_fail_on_service_error)
    else:
        echo_error(result.message)
        return exit_with_code(ExitCode.BACKEND_ERROR, no_fail_on_service_error)


def _process_failure_to_exit_code(run_execution: AssessmentJobDTO):
    if run_execution.last_step == StepFunctionStepDTO.PROCESS_BUILDING_ENV_CONTEXT \
            and run_execution.error_message:
        return ExitCode.CONTEXT_ERROR
    return ExitCode.BACKEND_ERROR


def _get_account_config(cloudrail_repository,
                        cloud_account_id: Optional[str],
                        cloud_account_name: Optional[str],
                        no_fail_on_service_error: bool) -> AccountConfigDTO:
    cloud_account_id = cloud_account_id or ''
    cloud_account_name = cloud_account_name or ''
    result = cloudrail_repository.list_cloud_accounts()
    if not result.success:
        echo_error(result.message)
        exit_with_code(ExitCode.BACKEND_ERROR, no_fail_on_service_error)
    account_configs: List[AccountConfigDTO] = result.message
    if len(account_configs) == 0:
        echo_error('Before executing a \"run\", please add your cloud account by using the \"cloud-account add\" command')
        exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)
    if len(account_configs) > 1 and not cloud_account_id and not cloud_account_name:
        echo_error('You have added several cloud accounts to Cloudrail. Please provide “--cloud-account-id” with the cloud account’s ID.')
        exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)
    if len(account_configs) == 1 and not cloud_account_id and not cloud_account_name:
        return account_configs[0]
    for account_config in account_configs:
        if account_config.cloud_account_id == cloud_account_id.strip() or account_config.name == cloud_account_name.strip():
            return account_config
    echo_error('The cloud account ID you entered is not recognized.'
               '\nPlease check it is valid, and if so, add it via the "cloud-account add" command.')
    return exit_with_code(ExitCode.INVALID_INPUT, no_fail_on_service_error)


def _get_account_policies(cloudrail_repository: CloudrailCliService,
                          account_config: AccountConfigDTO,
                          no_fail_on_service_error: bool) -> List[PolicyDTO]:
    response = cloudrail_repository.list_policies([account_config.id])
    if not response.success:
        echo_error(response.message)
        exit_with_code(ExitCode.BACKEND_ERROR, no_fail_on_service_error)
    policies: List[PolicyDTO] = response.message
    return policies


def _get_progress_messages(last_step: StepFunctionStepDTO, current_step: StepFunctionStepDTO = None) -> List[str]:
    messages = {5: 'Building simulated graph model, representing how the cloud account will look like if the plan were to be applied...',
                6: 'Running context-aware rules...',
                7: 'Returning results, almost done!'}
    steps: List[StepFunctionStepDTO] = StepFunctionStepDTO.get_steps()
    last_step_index = steps.index(last_step) if last_step else 0
    current_step_index = steps.index(current_step) if current_step else 0
    return [messages.get(i) for i in range(last_step_index + 1, current_step_index + 1) if messages.get(i)]


def _save_result_to_file(result: str, output_file: str) -> None:
    full_path = os.path.join(os.getcwd(), output_file)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    click.echo(f'Saving formatter results to: {output_file}')
    with open(full_path, 'w') as writer:
        writer.write(result)


def _show_origin_warning_message(origin: RunOriginDTO) -> None:
    if origin == RunOriginDTO.CI:
        return
    upper_os_env = {k.upper(): v for k, v in os.environ.items()}
    show_warning = False
    if upper_os_env.get('CI', '').lower() == 'true':
        show_warning = True
    known_keys = {'JOB_NAME', 'BUILD_NUMBER', 'CIRCLECI', 'TRAVIS', 'CI_JOB_NAME', 'CODEBUILD_BUILD_ID'}
    show_warning = show_warning or any(upper_os_env.get(known_key) for known_key in known_keys)
    if show_warning:
        click.echo("NOTE: You are running Cloudrail under CI but without the '--origin' parameter."
                   "\nIt is best to provide that parameter to improve reporting within the Cloudrail Web User Interface.")


def _show_account_collect_message(refresh_cloud_account_snapshot: bool,
                                  assessment_job: AssessmentJobDTO,
                                  account_config: AccountConfigDTO,
                                  spinner: SpinnerWrapper):
    if refresh_cloud_account_snapshot:
        spinner.start('Cloudrail Service is refreshing its cached snapshot of cloud account {}, '
                      'this may take a few minutes...'.format(account_config.cloud_account_id))
    elif assessment_job.run_type == RunTypeDTO.COLLECT_PROCESS_TEST:
        account_status = account_config.status
        if account_status == AccountStatusDTO.INITIAL_ENVIRONMENT_MAPPING:
            spinner.start('Cloudrail is still collecting the first snapshot of your cloud account. Please wait. '
                          'This will not be needed in future runs as a cache version is maintained and refreshed every 1 hour...')
        else:
            spinner.start('A recent attempt to collect a snapshot of your cloud account failed. '
                          'Therefore, Cloudrail is now attempting to collect a fresh snapshot of your cloud account. Please wait. '
                          'Normally, this is not needed, as a cache version is maintained and refreshed every 1 hour...')
    else:
        spinner.start('Cloudrail Service accessing the latest cached snapshot of cloud account {}. '
                      'Timestamp: {}...'.format(account_config.cloud_account_id, account_config.last_collected_at))
    spinner.succeed()


def exit_on_failure(cloudrail_repository: CloudrailCliService,
                    exit_code: ExitCode,
                    upload_logs: bool,
                    no_upload_log: bool,
                    origin: RunOriginDTO,
                    is_tty: bool,
                    job_id: Optional[str] = None,
                    no_fail_on_service_error: Optional[bool] = None):
    if not job_id:
        job_id = str(uuid.uuid4())
    offer_to_upload_log_and_exit(cloudrail_repository, exit_code, upload_logs, no_upload_log, origin,
                                 is_tty, job_id, 'run', no_fail_on_service_error)

from typing import Optional, List

from api.dtos.account_config_dto import AccountConfigDTO
from api.dtos.run_execution_dto import StepFunctionStepDTO

COLLECT_ERROR_MESSAGE = 'Cloudrail is not able to access the cloud account you have configured. \nThis is most likely due to permissions missing' \
                        ' from the role, or another configuration issue.' \
                        '\nPlease remove role \'{}\' and re-create using the CloudFormation or ' \
                        'Terraform files generated when you added your cloud account.' \
                        '\nYou can re-add the account using the Cloudrail web interface (https://web.cloudrail.app) ' \
                        'or with the \'cloudrail cloud-account add\' command.'
GENERIC_ERROR_MESSAGE = 'Cloudrail has encountered an unexpected error.\nA log has been stored with the Cloudrail Service.'
SERVICE_ERROR_MESSAGE = "\nCloudrail will not conduct its analysis due to this error. Exit code 0 returned," \
                        " due to '--no-fail-on-service-error' being set."
SERVICE_ERROR_NO_FAIL_ON_SERVICE_ERROR_MESSAGE = "\nDue to this error, Cloudrail CLI returns an exit code of {}. " \
                                                 "\nIf you would like to ignore such errors, use the '--no-fail-on-service-error' flag." \
                                                 " Note that Cloudrail cannot conduct its analysis successfully when such errors occur."
JOB_ID_MESSAGE = 'and mention job_id \'{}\'.'
CONTACT_INDENI_MESSAGE = 'Questions? Contact us through https://indeni.com/cloudrail-user-support'
FAILED_TO_CONVERT_PLAN_TO_JSON_HEADER_MESSAGE = 'Failed to convert plan to json.'
FAILED_TO_PROCESS_PLAN_JSON_HEADER_MESSAGE = 'Failed to process plan json.'
MISSING_API_KEY_MESSAGE = 'Missing API key. Please provide using one of the following methods:' \
                          '\n1. Add environment variable "CLOUDRAIL_API_KEY=<your_api_key>".' \
                          '\n2. Set config field using "cloudrail config set api_key=<your_api_key>".' \
                          '\n3. Pass api-key in the command "--api-key <your_api_key>".'

OFFER_TO_UPLOAD_LOGS_WORKSTATION_MESSAGE = '\nWe apologize as this error is unexpected.' \
                                           ' If you would like, this CLI tool can upload data that will help us troubleshoot the problem. ' \
                                           'The data will include the container’s log of this execution. \nWould you like to [R]eview the ' \
                                           'log before uploading, [U]ploading without reviewing it, or [N]ot upload the log at all? ' \
                                           '\nIn the future, you can include flags to automate the response to this question (\'--upload-log\'' \
                                           ' or \'--no-upload-log\'). (R/U/N)'
OFFER_TO_UPLOAD_LOGS_CI_MESSAGE = '\nWe apologize as this error is unexpected. ' \
                                  'If you would like, this CLI tool can upload data that will help us troubleshoot ' \
                                  'the problem. Re-run this command with \'--upload-log\'. You can include that flag ' \
                                  'on all runs, and only execution failures will have the logs uploaded.'


def generate_process_failure_message(error_message: Optional[str], job_id: Optional[str]):
    if error_message:
        messages = [GENERIC_ERROR_MESSAGE, error_message]
    else:
        messages = [GENERIC_ERROR_MESSAGE]
    return _append_contact_info_suffix(messages, job_id)


def generate_convert_terraform_plan_to_json_failure_message(error_message: Optional[str], job_id: Optional[str] = None):
    return generate_simple_message(error_message, job_id, FAILED_TO_CONVERT_PLAN_TO_JSON_HEADER_MESSAGE)


def generate_process_plan_json_failure_message(error_message: Optional[str], job_id: Optional[str] = None):
    return generate_simple_message(error_message, job_id, FAILED_TO_PROCESS_PLAN_JSON_HEADER_MESSAGE)


def generate_simple_message(error_message: Optional[str], job_id: Optional[str] = None, header: Optional[str] = None):
    if header:
        message = [header]
    else:
        message = []
    if error_message:
        message.append(error_message)
    else:
        message.append(GENERIC_ERROR_MESSAGE)
    return _append_contact_info_suffix(message, job_id)


def generate_collect_failure_message(account_config_dto: Optional[AccountConfigDTO], job_id: Optional[str]):
    if account_config_dto:
        message = COLLECT_ERROR_MESSAGE.format(account_config_dto.role_name)
    else:
        message = GENERIC_ERROR_MESSAGE
    return _append_contact_info_suffix([message], job_id)


def generate_failure_message(run_execution_step: StepFunctionStepDTO,
                             error_message: Optional[str],
                             job_id: str,
                             account_config_dto: AccountConfigDTO):
    if run_execution_step in (StepFunctionStepDTO.COLLECT, StepFunctionStepDTO.WAIT_FOR_COLLECT):
        return generate_collect_failure_message(account_config_dto, job_id)
    else:
        return generate_process_failure_message(error_message, job_id)


def _append_contact_info_suffix(messages: List[str], job_id: Optional[str]) -> str:
    if job_id:
        contact_message = f'{CONTACT_INDENI_MESSAGE} {JOB_ID_MESSAGE.format(job_id)}'
    else:
        contact_message = CONTACT_INDENI_MESSAGE
    messages.append(contact_message)
    return '\n\n'.join(messages)

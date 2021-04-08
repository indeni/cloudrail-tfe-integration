import logging
import os
from typing import List

from api.dtos.run_execution_dto import RunOriginDTO
from api.dtos.user_dto import UserWithTokenDTO, UserDTO, ApiKeyDTO
from api_client.cloudrail_api_client import CloudrailApiClient
from cli_configuration import CliConfiguration, CliConfigurationKey
from error_messages import MISSING_API_KEY_MESSAGE
from service.service_response import ServiceResponse, ServiceResponseFactory

logger = logging.getLogger('cli')

SPLIT_SIZE_BYTES = 1024 * 1024


class CloudrailCliService:
    def __init__(self, api_client: CloudrailApiClient,
                 configuration: CliConfiguration = None):
        self.api_client = api_client
        self.config = configuration or CliConfiguration()
        self._api_key = os.getenv('CLOUDRAIL_API_KEY') or self.config.get(CliConfigurationKey.API_KEY)

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        self._api_key = api_key

    def register(self, email: str, password: str, first_name: str, last_name: str) -> ServiceResponse:
        api_response = self.api_client.register(email, password, first_name, last_name)
        if api_response.success:
            user_response_dto: UserDTO = api_response.data
            logging.info('User registered successfully')
            self.config.customer_id = user_response_dto.customer_id
            api_response = self.api_client.login(email, password)
            if api_response.success:
                user_token_dto: UserWithTokenDTO = api_response.data
                api_response = self.api_client.generate_api_key(email, user_token_dto.access_token)
                if api_response.success:
                    api_key_dto: ApiKeyDTO = api_response.data
                    logging.info('Generate api key successfully')
                    self.config.set(CliConfigurationKey.API_KEY, api_key_dto.api_key)
                    return ServiceResponseFactory.success('Successfully register')
        return ServiceResponseFactory.failed(api_response.message)

    def unregister(self, email: str, password: str) -> ServiceResponse:
        return self._unregister(lambda: self.api_client.unregister(email, password), 'unregister')

    def _unregister(self, api_action, custom_log_message: str) -> ServiceResponse:
        api_response = api_action()
        if api_response.success:
            unregister_response: str = api_response.data
            logging.info(unregister_response)
            self.api_key = None
            self.config.clear_all()
            return ServiceResponseFactory.success(unregister_response)
        else:
            logging.error('failed to {0}'.format(custom_log_message))
            return ServiceResponseFactory.failed(api_response.message)

    def list_cloud_accounts(self, query: str = None) -> ServiceResponse:
        # pylint: disable=W0108
        return self._call_api_client(lambda api_key: self.api_client.list_accounts(api_key, query=query))

    def list_policies(self, account_config_ids: List[str]) -> ServiceResponse:
        # pylint: disable=W0108
        return self._call_api_client(lambda api_key: self.api_client.list_policies(api_key, account_config_ids=account_config_ids))

    def remove_cloud_account(self, account_id: str) -> ServiceResponse:
        return self._call_api_client(lambda api_key: self.api_client.remove_cloud_account(api_key, account_id))

    def add_cloud_account(self, account_name: str, account_id: str, pull_interval: int) -> ServiceResponse:
        return self._call_api_client(
            lambda api_key: self.api_client.add_cloud_account(api_key, account_name, account_id, pull_interval, True, True))

    def get_run_results(self, job_id: str) -> ServiceResponse:
        return self._call_api_client(lambda api_key: self.api_client.get_run_results(api_key, job_id))

    def run(self,
            account_config_id: str,
            origin: RunOriginDTO = RunOriginDTO.WORKSTATION,
            build_link: str = '',
            execution_source_identifier: str = '',
            run_collect: bool = str):
        if os.getenv('CLOUDRAIL_SKIP_COLLECT') is not None:
            skip_collect = os.getenv('CLOUDRAIL_SKIP_COLLECT').lower() == 'true'
        else:
            skip_collect = False
        return self._call_api_client(lambda api_key: self.api_client.run(api_key,
                                                                         run_collect,
                                                                         account_config_id,
                                                                         origin,
                                                                         build_link,
                                                                         execution_source_identifier,
                                                                         skip_collect))

    def submit_terraform_context(self, show_output: str, job_id: str):
        return self._call_api_client(lambda api_key: self.api_client.submit_terraform_context(api_key,
                                                                                              job_id,
                                                                                              show_output))

    def submit_failure(self, failure_info: str, job_id: str):
        return self._call_api_client(lambda api_key: self.api_client.submit_failure(api_key,
                                                                                    job_id,
                                                                                    failure_info))

    def get_run_status(self, job_id: str):
        return self._call_api_client(lambda api_key: self.api_client.get_run_status(api_key, job_id))

    def get_my_customer_data(self) -> ServiceResponse:
        return self._call_api_client(lambda api_key: self.api_client.get_my_customer_data(api_key=api_key))

    def list_aws_supported_services(self):
        return self._call_api_client(lambda _: self.api_client.list_aws_supported_services())

    def list_checkov_supported_services(self):
        return self._call_api_client(lambda _: self.api_client.list_checkov_supported_services())

    def upload_log(self, log: str, job_id: str, command: str):
        return self._call_api_client(lambda api_key: self.api_client.upload_log(log, job_id, command, api_key))

    def _call_api_client(self, api_action):
        if self.api_key is None:
            return ServiceResponseFactory.failed(MISSING_API_KEY_MESSAGE)
        try:
            api_response = api_action(self.api_key)
        except OSError:
            return ServiceResponseFactory.failed("""The Cloudrail Service cannot be reached at this time.
                Please check your network connectivity or reach out to us by visiting https://indeni.com/cloudrail-user-support/""")
        if api_response.success:
            return ServiceResponseFactory.success(api_response.data)
        return ServiceResponseFactory.failed(api_response.message)

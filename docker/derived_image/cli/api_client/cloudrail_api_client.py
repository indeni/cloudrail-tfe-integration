import json
import logging
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Union, List, Optional

from api.dtos.account_config_dto import AccountConfigDTO, AccountConfigAddDTO, AccountConfigUpdateDTO
from api.dtos.assessment_result_dto import AssessmentResultDTO
from api.dtos.customer_dto import CustomerDTO
from api.dtos.environment_context_dto import EnvironmentContextResultDTO
from api.dtos.filter_block_dto import FilterBlockDTO
from api.dtos.pagination_result_dto import PaginationResultDTO
from api.dtos.policy_dto import PolicyDTO, PolicyUpdateDTO, PolicyRuleDTO, PolicyRuleUpdateDTO, PolicyAddDTO, PolicyRuleBulkAddDataDTO
from api.dtos.rule_info_dto import RuleInfoDTO, RuleUpdateDTO, RuleBulkUpdateDTO
from api.dtos.rule_result_dto import RuleResultDTO
from api.dtos.rule_task_dto import RuleTaskDTO
from api.dtos.run_execution_dto import AssessmentJobDTO, RunOriginDTO
from api.dtos.supported_services_response_dto import SupportedAwsServicesResponseDTO, SupportedCheckovServicesResponseDTO
from api.dtos.user_dto import UserDTO, UserWithTokenDTO, UserLoginDTO, UserRegisterDTO, UserUnregisterDTO, ApiKeyDTO, UserUpdateDTO, \
    UserChangePasswordDTO, UserInviteDTO, UserInvitationSummaryDTO, UserRegisterWithInvitationDTO, UserResetPasswordRequestSummaryDTO, \
    UserResetPasswordDTO, UserResetPasswordRequestDTO
from api_client.contract.cloudrail_api_response import BaseCloudrailResponse, CloudrailErrorResponse, \
    CloudrailSuccessJsonResponse, CloudrailSuccessDataResponse
from api_client.external_api_client import ExternalApiClient
from cli_configuration import CliConfiguration, CliConfigurationKey


@dataclass
class APIResult:
    success: bool
    response: Union[str, dict]


class CloudrailApiClient(ExternalApiClient):
    LOGIN_PATH: str = '/users/login'
    LOGOUT_PATH: str = '/users/logout'
    USER_ID_PATH: str = '/users/{0}'
    USER_ID_CHANGE_PASSWORD_PATH: str = '/users/{0}/password/change'
    USER_RESET_PASSWORD_REQUEST_PATH: str = '/users/password/reset/request'
    USER_RESET_PASSWORD_CONFIRM_PATH: str = '/users/password/reset/confirm'
    USERS: str = '/users/'
    USER_GET_MY_PROFILE_PATH: str = '/users/me'
    USER_INVITE_PATH: str = '/users/invite'
    REGISTER_PATH: str = '/users/register'
    COMPLETE_REGISTRATION_PATH: str = '/users/complete_registration'
    API_KEY_PATH: str = '/users/{0}/apikey'
    UN_REGISTER_PATH: str = '/users/unregister'
    ACCOUNTS_PATH: str = '/accounts?query={0}&sort_by={1}&sort_direction={2}'
    ADD_ACCOUNTS_PATH: str = '/accounts?verify={0}&collect={1}'
    ACCOUNT_ID_PATH: str = '/accounts/{0}'
    POLICY_ID_PATH: str = '/policies/{0}'
    ADD_POLICY_PATH: str = '/policies'
    LIST_POLICIES_PATH: str = '/policies?{0}&query={1}&sort_by={2}&sort_direction={3}'
    ADD_POLICIES_ACCOUNTS: str = '/policies/{0}/accounts'
    DELETE_POLICIES_ACCOUNT: str = '/policies/{0}/accounts/{1}'
    POLICY_RULES_PATH: str = '/policies/{0}/rules'
    ADD_BULK_POLICIES_RULES: str = '/policies/rules'
    POLICIES_RULES_ID: str = '/policies/{0}/rules/{1}'
    RUN: str = '/run?run_collect={0}&account_config_id={1}&origin={2}&build_link={3}&execution_source_identifier={4}&skip_collect={5}'
    SUBMIT_CONTEXT = '/run/{0}/terraform_context_result'
    RUN_RESULTS: str = '/run/{0}/results'
    RUN_STATUS: str = '/run/{0}/status'
    UPLOAD_LOG: str = '/logs/cli?job_id={0}&command={1}'
    CUSTOMERS_PATH: str = '/customers/{0}'
    CUSTOMERS_API_KEY_PATH: str = '/customers/me/apikey'
    CUSTOMERS_ME_PATH: str = '/customers/me'
    CUSTOMERS__TERRAFORM_TEMPLATE_PATH: str = '/customers/{0}/terraform_template'
    LIST_RULES_PATH: str = '/rules?query={0}&policy_id={1}&has_policy_association={2}'
    RULE_ID_PATH: str = '/rules/{0}'
    UPDATE_RULES_PATH: str = '/rules'
    RULE_FILTERS_PATH: str = '/rules/filters'
    RULE_RESULTS_PATH: str = '/rules/results?assessment_id={0}&result_status={1}&query={2}&start_date={3}&end_date={4}&page={5}&items_per_page={6}'
    ASSESSMENTS_PATH: str = '/assessments?query={0}&start_date={1}&end_date={2}&page={3}&items_per_page={4}&sort_direction={5}&sort_by={6}'
    ASSESSMENTS_ID_PATH: str = '/assessments/{0}'
    RULES_TASKS_PATH: str = '/task_center/rules/tasks?query={0}'
    RULES_TASK_RESULTS_PATH: str = '/task_center/rules/{0}/results'
    VERSION_PATH: str = '/version'
    AWS_SUPPORTED_SERVICES: str = '/supported_services/aws'
    CHECKOV_SUPPORTED_SERVICES: str = '/supported_services/checkov'
    FEATURE_FLAGS_PATH: str = '/feature_flags?{}'

    def __init__(self, service_endpoint: str = None):
        endpoint = service_endpoint \
                   or os.getenv('CLOUDRAIL_API_GATEWAY') \
                   or CliConfiguration().get(CliConfigurationKey.ENDPOINT) \
                   or 'https://api.cloudrail.app'
        ExternalApiClient.__init__(self, endpoint)

    def login(self, email: str, password: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.post(self.LOGIN_PATH,
                                                          UserLoginDTO(email=email,
                                                                       password=password).to_dict()),
                                        custom_log_message='login')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=UserWithTokenDTO.from_dict(api_result.response))

    def logout(self, access_token: str = None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.LOGOUT_PATH),
                                        custom_log_message='logout',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def get_my_profile(self, access_token: str = None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.USER_GET_MY_PROFILE_PATH),
                                        custom_log_message='get my profile',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=UserDTO.from_dict(api_result.response))

    def list_users(self, access_token: str = None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.USERS),
                                        custom_log_message='list users',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        users = [UserDTO.from_dict(user) for user in api_result.response]
        return CloudrailSuccessJsonResponse(data=users)

    def update_user(self, email: str, user_update_dto: UserUpdateDTO, access_token: str = None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.patch(self.USER_ID_PATH.format(email), user_update_dto.to_dict()),
                                        custom_log_message='update user',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=UserDTO.from_dict(api_result.response))

    def change_password(self, email: str, user_update_dto: UserChangePasswordDTO, access_token: str = None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.patch(self.USER_ID_CHANGE_PASSWORD_PATH.format(email), user_update_dto.to_dict()),
                                        custom_log_message='change user password',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def request_reset_password(self, reset_password_request_dto: UserResetPasswordRequestDTO) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.post(self.USER_RESET_PASSWORD_REQUEST_PATH,
                                                          reset_password_request_dto.to_dict()),
                                        custom_log_message='reset password request')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=UserResetPasswordRequestSummaryDTO.from_dict(api_result.response))

    def confirm_reset_password(self, reset_password_dto: UserResetPasswordDTO) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.post(self.USER_RESET_PASSWORD_CONFIRM_PATH,
                                                          reset_password_dto.to_dict()),
                                        custom_log_message='reset password confirm')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def delete_user(self, email: str, access_token: str = None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.delete(self.USER_ID_PATH.format(email)),
                                        custom_log_message='delete user',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def get_user(self, email: str, access_token: str = None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.USER_ID_PATH.format(email)),
                                        custom_log_message='get user',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=UserDTO.from_dict(api_result.response))

    def register(self, email: str, password: str, first_name: str, last_name: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.post(self.REGISTER_PATH,
                                                          UserRegisterDTO(email=email,
                                                                          password=password,
                                                                          first_name=first_name,
                                                                          last_name=last_name).to_dict()),
                                        custom_log_message='register')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=UserDTO.from_dict(api_result.response))

    def invite_user(self, user_invite_dto: List[UserInviteDTO], access_token: str):
        api_result = self._send_request(lambda: self.post(self.USER_INVITE_PATH,
                                                          data=UserInviteDTO.schema().dumps(user_invite_dto, many=True)),
                                        custom_log_message='invite user',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        invites_summary = [UserInvitationSummaryDTO.from_dict(user_invite_summary) for user_invite_summary in api_result.response]
        return CloudrailSuccessJsonResponse(data=invites_summary)

    def complete_registration(self, register_with_invitation: UserRegisterWithInvitationDTO):
        api_result = self._send_request(lambda: self.patch(self.COMPLETE_REGISTRATION_PATH,
                                                           register_with_invitation.to_dict()),
                                        custom_log_message='complete user registration')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=UserDTO.from_dict(api_result.response))

    def generate_api_key(self, email: str, access_token: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.post(self.API_KEY_PATH.format(email)),
                                        custom_log_message='generate api key',
                                        access_token=access_token)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=ApiKeyDTO.from_dict(api_result.response))

    def get_api_key(self, email: str, access_token: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.API_KEY_PATH.format(email)),
                                        custom_log_message='get api key',
                                        access_token=access_token)

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        if api_result.response:
            return CloudrailSuccessJsonResponse(data=ApiKeyDTO.from_dict(api_result.response))
        else:
            return CloudrailSuccessJsonResponse()

    def unregister(self, email: str, password: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.post(self.UN_REGISTER_PATH,
                                                          UserUnregisterDTO(email=email, password=password).to_dict()),
                                        custom_log_message='unregister')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def list_accounts(self, api_key: str,
                      query: Optional[str] = None,
                      sort_by: Optional[str] = None,
                      sort_direction: Optional[str] = None) -> BaseCloudrailResponse:

        api_result = self._send_request(lambda: self.get(self.ACCOUNTS_PATH.format(query or '',
                                                                                   sort_by or '',
                                                                                   sort_direction or '')), api_key, 'list accounts')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        account_configs = [AccountConfigDTO.from_dict(account) for account in api_result.response]
        return CloudrailSuccessJsonResponse(data=account_configs)

    def update_account(self, api_key: str, account_config_id: str, account_name: str) -> BaseCloudrailResponse:
        payload = AccountConfigUpdateDTO(name=account_name).to_dict()
        api_result = self._send_request(lambda: self.patch(self.ACCOUNT_ID_PATH.format(account_config_id), payload), api_key, 'update cloud account')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        account_config = AccountConfigDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=account_config)

    def get_account(self, api_key: str, account_config_id: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.ACCOUNT_ID_PATH.format(account_config_id)), api_key, 'get cloud account')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        account_config = AccountConfigDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=account_config)

    def list_policies(self,
                      api_key: str,
                      account_config_ids: List[str] = None,
                      query: str = '',
                      sort_by: str = '',
                      sort_direction: str = '') -> BaseCloudrailResponse:
        account_config_ids_query = ','.join(['account_config_id={}'.format(account_config_id)
                                             for account_config_id in account_config_ids or []]) or ''
        api_result = self._send_request(lambda: self.get(self.LIST_POLICIES_PATH.format(account_config_ids_query,
                                                                                        query,
                                                                                        sort_by,
                                                                                        sort_direction)), api_key, 'list policies')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policies = [PolicyDTO.from_dict(policy) for policy in api_result.response]
        return CloudrailSuccessJsonResponse(data=policies)

    def get_policy(self, api_key: str, policy_id: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.POLICY_ID_PATH.format(policy_id)), api_key, 'get policy')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policy = PolicyDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=policy)

    def update_policy(self, api_key: str, policy_id: str, policy_update_dto: PolicyUpdateDTO):
        api_result = self._send_request(lambda: self.patch(self.POLICY_ID_PATH.format(policy_id), policy_update_dto.to_dict()), api_key,
                                        'update policy')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policy = PolicyDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=policy)

    def add_policy_account_configs(self, api_key: str, policy_id: str, account_config_ids: List[str]):
        api_result = self._send_request(lambda: self.patch(self.ADD_POLICIES_ACCOUNTS.format(policy_id), data=json.dumps(account_config_ids)),
                                        api_key, 'add policy account')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policy = PolicyDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=policy)

    def delete_policy_account_config(self, api_key: str, policy_id: str, account_config_id: str):
        api_result = self._send_request(lambda: self.delete(self.DELETE_POLICIES_ACCOUNT.format(policy_id, account_config_id)),
                                        api_key,
                                        'remove policy_account_config')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def add_policy_rules(self, api_key: str, policy_id: str, policy_rules: List[PolicyRuleDTO]):
        policy_rules = PolicyRuleDTO.schema().dumps(policy_rules, many=True)
        api_result = self._send_request(lambda: self.patch(self.POLICY_RULES_PATH.format(policy_id), data=policy_rules), api_key,
                                        'add policy rules')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policy = PolicyDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=policy)

    def add_bulk_policy_rules(self, api_key: str, policy_rules: List[PolicyRuleBulkAddDataDTO]):
        policy_rules = PolicyRuleBulkAddDataDTO.schema().dumps(policy_rules, many=True, default=lambda o: o.__dict__)
        api_result = self._send_request(lambda: self.patch(self.ADD_BULK_POLICIES_RULES, data=policy_rules), api_key,
                                        'add bulk policy rules')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policies = [PolicyDTO.from_dict(policy) for policy in api_result.response]
        return CloudrailSuccessJsonResponse(data=policies)

    def update_policy_rule(self, api_key: str, policy_id: str, rule_id: str, policy_rule_update: PolicyRuleUpdateDTO):
        api_result = self._send_request(lambda: self.patch(self.POLICIES_RULES_ID.format(policy_id, rule_id), policy_rule_update.to_dict()),
                                        api_key, 'add policy account')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policy = PolicyDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=policy)

    def delete_policy_rule(self, api_key: str, policy_id: str, rule_id: str):
        api_result = self._send_request(lambda: self.delete(self.POLICIES_RULES_ID.format(policy_id, rule_id)),
                                        api_key,
                                        'remove policy rule')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def delete_policy_rules(self, api_key: str, policy_id: str, rule_ids: List[str]):
        rule_ids_query = '&'.join([f'rule_id={rule_id}' for rule_id in rule_ids])
        path = f'{self.POLICY_RULES_PATH.format(policy_id)}?{rule_ids_query}'
        api_result = self._send_request(lambda: self.delete(path),
                                        api_key,
                                        'remove policy rules')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def remove_cloud_account(self, api_key: str, cloud_account_id: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.delete(self.ACCOUNT_ID_PATH.format(cloud_account_id)),
                                        api_key,
                                        'remove cloud account')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def remove_policy(self, api_key: str, policy_id: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.delete(self.POLICY_ID_PATH.format(policy_id)),
                                        api_key,
                                        'remove policy')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def add_cloud_account(self, api_key: str, account_name: str, account_id: str,
                          pull_interval: int, verify: bool, collect: bool) -> BaseCloudrailResponse:
        payload = AccountConfigAddDTO(
            name=account_name,
            interval_seconds=pull_interval,
            cloud_account_id=account_id).to_dict()
        api_result = self._send_request(lambda: self.post(self.ADD_ACCOUNTS_PATH.format(verify, collect), payload), api_key, 'add cloud account')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        account_config = AccountConfigDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=account_config)

    def add_policy(self, api_key: str, policy_dto: PolicyAddDTO) -> BaseCloudrailResponse:
        payload = policy_dto.to_dict()
        api_result = self._send_request(lambda: self.post(self.ADD_POLICY_PATH, payload), api_key, 'add policy')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        policy = PolicyDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=policy)

    def run(self,
            api_key: str,
            run_collect: bool,
            account_config_id: str,
            origin: RunOriginDTO,
            build_link: str,
            execution_source_identifier: str,
            skip_collect: bool) -> BaseCloudrailResponse:

        path = self.RUN.format(run_collect.__str__().lower(),
                               account_config_id,
                               origin.value,
                               build_link or '',
                               execution_source_identifier or '',
                               skip_collect.__str__().lower())
        api_result = self._send_request(
            lambda: self.post(path), api_key, 'run')

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)

        return CloudrailSuccessJsonResponse(data=AssessmentJobDTO.from_dict(api_result.response))

    def submit_terraform_context(self,
                                 api_key: str,
                                 job_id: str,
                                 show_output: str) -> BaseCloudrailResponse:
        try:
            json.loads(show_output)
        except Exception as ex:
            self.submit_failure(api_key, job_id, str(ex))
            return CloudrailErrorResponse(message="failed to serialize json from Terraform output file")
        data = EnvironmentContextResultDTO(True, show_output)
        path = self.SUBMIT_CONTEXT.format(job_id)
        api_result = self._send_request(
            lambda: self.post(path, data.to_dict()), api_key, 'submit Terraform output')

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def submit_failure(self,
                       api_key: str,
                       job_id: str,
                       failure: str) -> BaseCloudrailResponse:
        data = EnvironmentContextResultDTO(False, error=failure)
        path = self.SUBMIT_CONTEXT.format(job_id)
        api_result = self._send_request(
            lambda: self.post(path, data.to_dict()), api_key, 'submit failure')

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def get_run_results(self, api_key: str, job_id: str) -> BaseCloudrailResponse:
        path = self.RUN_RESULTS.format(job_id)
        api_result = self._send_request(lambda: self.get(path), api_key, 'get run result')

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rule_results = [RuleResultDTO.from_dict(rule_result) for rule_result in api_result.response]
        return CloudrailSuccessJsonResponse(data=rule_results)

    def list_rule_results(self,
                          api_key: str,
                          assessment_id: Optional[str] = None,
                          result_status: Optional[str] = None,
                          start_date: Optional[int] = None,
                          end_date: Optional[int] = None,
                          page: Optional[int] = None,
                          items_per_page: Optional[int] = None,
                          query: Optional[str] = None
                          ):
        path = self.RULE_RESULTS_PATH.format(assessment_id or '',
                                             result_status or '',
                                             query or '',
                                             start_date or '',
                                             end_date or '',
                                             page or '',
                                             items_per_page or '')
        api_result = self._send_request(lambda: self.get(path), api_key, 'list rule result')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rule_results = PaginationResultDTO.from_dict(api_result.response)
        rule_results.page_results = [RuleResultDTO.from_dict(rl) for rl in rule_results.page_results]
        return CloudrailSuccessJsonResponse(data=rule_results)

    def list_assessments(self,
                         api_key: str,
                         query: Optional[str] = None,
                         sort_direction: Optional[str] = None,
                         sort_by: Optional[str] = None,
                         start_date: Optional[int] = None,
                         end_date: Optional[int] = None,
                         page: Optional[int] = None,
                         items_per_page: Optional[int] = None
                         ):
        path = self.ASSESSMENTS_PATH.format(query or '',
                                            start_date or '',
                                            end_date or '',
                                            page or '',
                                            items_per_page or '',
                                            sort_direction or '',
                                            sort_by or '')
        api_result = self._send_request(lambda: self.get(path), api_key, 'list assessments')

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        assessments = PaginationResultDTO.from_dict(api_result.response)
        assessments.page_results = [AssessmentResultDTO.from_dict(rl) for rl in assessments.page_results]
        return CloudrailSuccessJsonResponse(data=assessments)

    def get_assessment(self, api_key: str, assessment_id: str):
        path = self.ASSESSMENTS_ID_PATH.format(assessment_id)
        api_result = self._send_request(lambda: self.get(path), api_key, 'get assessment')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        assessment = AssessmentResultDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=assessment)

    def list_rules_tasks(self, api_key: str, query: Optional[str] = None):
        path = self.RULES_TASKS_PATH.format(query or '')
        api_result = self._send_request(lambda: self.get(path), api_key, 'list rule tasks')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rule_tasks = [RuleTaskDTO.from_dict(rule_task) for rule_task in api_result.response]
        return CloudrailSuccessJsonResponse(data=rule_tasks)

    def get_rules_task_results(self, api_key: str, rule_id: str):
        path = self.RULES_TASK_RESULTS_PATH.format(rule_id)
        api_result = self._send_request(lambda: self.get(path), api_key, 'get rule task results')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rule_tasks = [RuleResultDTO.from_dict(rule_result) for rule_result in api_result.response]
        return CloudrailSuccessJsonResponse(data=rule_tasks)

    def get_run_status(self, api_key: str, job_id: str) -> BaseCloudrailResponse:
        path = self.RUN_STATUS.format(job_id)
        api_result = self._send_request(lambda: self.get(path), api_key, 'get run status')

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=AssessmentJobDTO.from_dict(api_result.response))

    def _send_request(self, action, api_key: str = None, custom_log_message: str = '', access_token: str = None) -> APIResult:
        logging.debug(custom_log_message)
        if api_key:
            self.set_api_key(api_key)
        if access_token:
            self.set_access_token(access_token)
        try:
            response = action()
            self.unset_access_token()
            self.unset_api_key()

        except Exception:
            logging.exception(f'Failed to connect to the Cloudrail Service {self.api_base_url}')
            return APIResult(False, f'Failed to connect to the Cloudrail Service {self.api_base_url}')
        if response.status_code == HTTPStatus.NO_CONTENT or not response.text:
            return APIResult(True, '')

        response_data = None
        if 'application/json' in response.headers['content-type']:
            response_data = json.loads(response.text)
        elif response.headers['content-type'] == 'application/octet-stream':
            response_data = response.text
        else:
            return APIResult(False, 'Received unsupported content-type. Content-type can be application/json or text/plain')
        logging.debug('received data: {}'.format(response_data))

        if response.status_code != HTTPStatus.OK:
            if response.status_code == HTTPStatus.UNAUTHORIZED or response.status_code == HTTPStatus.FORBIDDEN:
                logging.error('Unauthorized request: {0}'.format(custom_log_message))
                return APIResult(False, 'Unauthorized. Please try to login again\n' + response_data['message'])

            message = 'Failed to {0}: {1}'.format(custom_log_message, response_data['message'])
            logging.error(message)
            return APIResult(False, message)

        return APIResult(True, response_data)

    def get_customer(self, customer_id, access_token=None, api_key=None):
        api_result = self._send_request(lambda: self.get(self.CUSTOMERS_PATH.format(customer_id)),
                                        custom_log_message='get customer',
                                        access_token=access_token,
                                        api_key=api_key)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        customer = CustomerDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=customer)

    def get_my_customer_data(self, access_token=None, api_key=None):
        api_result = self._send_request(lambda: self.get(self.CUSTOMERS_ME_PATH),
                                        custom_log_message='get my customer',
                                        access_token=access_token,
                                        api_key=api_key)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        customer = CustomerDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=customer)

    def generate_api_key_customer(self, access_token=None, api_key=None):
        api_result = self._send_request(lambda: self.post(self.CUSTOMERS_API_KEY_PATH),
                                        custom_log_message='generate api key customer',
                                        access_token=access_token,
                                        api_key=api_key)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=ApiKeyDTO.from_dict(api_result.response))

    def get_api_key_customer(self, access_token: str = None, api_key=None) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.CUSTOMERS_API_KEY_PATH),
                                        custom_log_message='get api key customer',
                                        access_token=access_token,
                                        api_key=api_key)

        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        if api_result.response:
            return CloudrailSuccessJsonResponse(data=ApiKeyDTO.from_dict(api_result.response))
        else:
            return CloudrailSuccessJsonResponse()

    def get_terraform_template(self, customer_id, access_token=None, api_key=None):
        api_result = self._send_request(lambda: self.get(self.CUSTOMERS__TERRAFORM_TEMPLATE_PATH.format(customer_id)),
                                        custom_log_message='get customer terraform template',
                                        access_token=access_token,
                                        api_key=api_key)
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessDataResponse(data=api_result.response)

    def list_rules(self,
                   api_key: str,
                   query: str = None,
                   policy_id: str = None,
                   has_policy_association: str = None) -> BaseCloudrailResponse:
        policy_id = policy_id or ''
        query = query or ''
        has_policy_association = has_policy_association or ''
        api_result = self._send_request(lambda: self.get(self.LIST_RULES_PATH.format(query, policy_id, has_policy_association)),
                                        api_key,
                                        'list rules')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rules = [RuleInfoDTO.from_dict(rule) for rule in api_result.response]
        return CloudrailSuccessJsonResponse(data=rules)

    def get_rule(self, api_key: str, rule_id: str) -> BaseCloudrailResponse:
        api_result = self._send_request(lambda: self.get(self.RULE_ID_PATH.format(rule_id)),
                                        api_key,
                                        'get rule')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rule = RuleInfoDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=rule)

    def update_rule(self, api_key: str, rule_id: str, rule_update_params: RuleUpdateDTO):
        api_result = self._send_request(lambda: self.patch(self.RULE_ID_PATH.format(rule_id), rule_update_params.to_dict()),
                                        api_key, 'update rule')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rule = RuleInfoDTO.from_dict(api_result.response)
        return CloudrailSuccessJsonResponse(data=rule)

    def update_rules(self, api_key: str, rule_updates_params: List[RuleBulkUpdateDTO]):
        rule_updates = RuleBulkUpdateDTO.schema().dumps(rule_updates_params, many=True)
        api_result = self._send_request(lambda: self.patch(self.UPDATE_RULES_PATH, data=rule_updates),
                                        api_key, 'update rules')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        rules = [RuleInfoDTO.from_dict(rule) for rule in api_result.response]
        return CloudrailSuccessJsonResponse(data=rules)

    def get_version(self):
        api_result = self._send_request(lambda: self.get(self.VERSION_PATH),
                                        custom_log_message='get version')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=api_result.response['version'])

    def list_aws_supported_services(self):
        api_result = self._send_request(lambda: self.get(self.AWS_SUPPORTED_SERVICES),
                                        custom_log_message='list aws supported services')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=SupportedAwsServicesResponseDTO.from_dict(api_result.response))

    def list_checkov_supported_services(self):
        api_result = self._send_request(lambda: self.get(self.CHECKOV_SUPPORTED_SERVICES),
                                        custom_log_message='list cechkov supported services')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=SupportedCheckovServicesResponseDTO.from_dict(api_result.response))

    def get_feature_flags(self, api_key: str, feature_flag_keys: List[str]):
        param = '&'.join([f'name={key}' for key in feature_flag_keys])
        api_result = self._send_request(lambda: self.get(self.FEATURE_FLAGS_PATH.format(param)), api_key, 'get feature flags')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse(data=api_result.response)

    def upload_log(self, log: str, job_id: str, command: str, api_key: str = None):
        api_result = self._send_request(
            lambda: self.post(self.UPLOAD_LOG.format(job_id, command), data=log), api_key, 'upload log')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        return CloudrailSuccessJsonResponse()

    def list_rule_filters(self, api_key: str):
        api_result = self._send_request(lambda: self.get(self.RULE_FILTERS_PATH), api_key, 'get feature flags')
        if not api_result.success:
            return CloudrailErrorResponse(message=api_result.response)
        blocks = [FilterBlockDTO.from_dict(block) for block in api_result.response]
        return CloudrailSuccessJsonResponse(data=blocks)

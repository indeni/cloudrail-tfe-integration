import copy
import json
import logging
import os
import shutil
import tempfile
import traceback
import uuid
from dataclasses import dataclass
from typing import Optional, List, Dict

from exceptions import TerraformShowException
from api.dtos.supported_services_response_dto import SupportedSectionDTO, FieldActionDTO, KnownFieldsDTO
from environment_context.common.ip_encryption_utils import encode_ips_in_json, EncryptionMode
from environment_context.common.terraform_service.terraform_output_validator import TerraformOutputValidator
from environment_context.common.terraform_service.terraform_plan_converter import TerraformPlanConverter
from rules.checkov.checkov_executor import CheckovExecutor, CheckovResult
from utils.customer_string_utils import CustomerStringUtils


@dataclass
class TerraformContextResult:
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class TerraformContextService:

    def __init__(self, terraform_plan_converter: TerraformPlanConverter, checkov_executor: CheckovExecutor = None):
        self.terraform_plan_converter = terraform_plan_converter
        self.checkov_executor = checkov_executor or CheckovExecutor()
        self.working_dir = None

    def convert_plan_to_json(self, terraform_plan_path: str, terraform_env_path: str) -> TerraformContextResult:
        try:
            logging.info('step 1 - copy Terraform data to temp folder')
            working_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            os.makedirs(working_dir)
            self.working_dir = working_dir
            logging.info('step 2 - Terraform plan to json')
            return TerraformContextResult(True, self._get_terraform_plan_json_file(terraform_plan_path, terraform_env_path, working_dir))
        except TerraformShowException as ex:
            logging.exception('error converting plan to json')
            self._clean_env()
            return TerraformContextResult(False, error=str(ex))
        except Exception as ex:
            logging.exception('error converting plan to json')
            self._clean_env()
            return TerraformContextResult(False, error=str(ex))

    def process_json_result(self,
                            plan_json_path: str,
                            services_to_include: Dict[str, SupportedSectionDTO],
                            checkov_results: Dict[str, List[CheckovResult]],
                            customer_id: str,
                            handshake_version: str):
        try:
            CustomerStringUtils.set_hashcode_salt(customer_id)
            with open(plan_json_path, 'r+') as file:
                dic = json.loads(file.read())
                result_dic = {'terraform_version': dic['terraform_version'],
                              'format_version': dic['format_version'],
                              'configuration': {'provider_config': dic['configuration'].get('provider_config', {}),
                                                'root_module': self._filter_root_module(dic['configuration'].get('root_module'))},
                              'resource_changes': [
                                  self._filter_resource(resource, services_to_include)
                                  for resource in dic['resource_changes'] if resource['type'] in services_to_include.keys()],
                              'checkov_results': checkov_results,
                              'handshake_version': handshake_version}
            return TerraformContextResult(True, encode_ips_in_json(json.dumps(result_dic, indent=4, default=vars),
                                                                   customer_id, EncryptionMode.ENCRYPT))
        except Exception as ex:
            logging.exception(f'error while filtering Terraform show output, ex={str(ex)}')
            traceback.print_tb(ex.__traceback__, limit=None, file=None)
            return TerraformContextResult(False, error=str(ex))
        finally:
            self._clean_env()

    @staticmethod
    def read_terraform_output_file(path: str) -> TerraformContextResult:
        try:
            with open(path, 'r') as reader:
                data = reader.read()
                TerraformOutputValidator.validate(data)
                return TerraformContextResult(True, data)
        except Exception as ex:
            logging.exception('error while converting json file to result')
            return TerraformContextResult(False, error=str(ex))

    def _get_terraform_plan_json_file(self,
                                      terraform_plan_path: str,
                                      terraform_env_path: str,
                                      working_dir: str) -> str:
        try:
            plan_json_path = self.terraform_plan_converter.convert_to_json(terraform_plan_path, terraform_env_path, working_dir)
            logging.info('terraform show ran successfully. output saved to {}'.format(plan_json_path))
            return plan_json_path
        except Exception as err:
            logging.warning('failed getting Terraform file', exc_info=1)
            raise err

    def _clean_env(self):
        if self.working_dir:
            shutil.rmtree(self.working_dir)
        self.working_dir = None

    def _filter_resource(self, resource: dict,
                         services_to_include: Dict[str, SupportedSectionDTO]):
        resource_type = resource['type']
        supported_section = self._get_normalized_supported_section(resource_type, services_to_include)
        return {'address': resource.get('address'), 'type': resource.get('type'),
                'name': resource.get('name'), 'mode': resource.get('mode'), 'provider_name': resource.get('provider_name'),
                'change': self._filter_change_dict(resource.get('change'), supported_section)}

    def _filter_change_dict(self, change: dict, supported_section: SupportedSectionDTO):
        return {'before': self._filter_fields(change.get('before'), supported_section),
                'after': self._filter_fields(change.get('after'), supported_section),
                'after_unknown': self._filter_fields(change.get('after_unknown'), supported_section),
                'actions': change.get('actions')}

    @classmethod
    def _filter_fields(cls, dic: dict, supported_section: SupportedSectionDTO):
        if not dic:
            return dic
        result = {}
        for key in dic.keys():
            value = dic[key]
            if supported_section.known_fields:
                if key.lower() in supported_section.known_fields.pass_values:
                    result[key] = cls._get_passed_field(key.lower(), value, supported_section)
                    continue
                if key.lower() in supported_section.known_fields.hash_values:
                    cls._add_to_dic_as_hash(key, value, result)
                    continue
            if supported_section.unknown_fields_action == FieldActionDTO.PASS:
                result[key] = value
                continue
            if supported_section.unknown_fields_action == FieldActionDTO.HASH:
                cls._add_to_dic_as_hash(key, value, result)
                continue
        return result

    @classmethod
    def _get_passed_field(cls, key, value, supported_section):
        known_key_value = supported_section.known_fields.pass_values.get(key)
        if known_key_value:
            if value is not None and not isinstance(value, list) and not isinstance(value, dict):
                return value
            if isinstance(value, list):
                return [cls._filter_fields(field, known_key_value) for field in value]
            if isinstance(value, dict):
                return cls._filter_fields(value, known_key_value)
        return value

    @staticmethod
    def _add_to_dic_as_hash(key: str, value: str, dic: dict):
        hash_key = f'{key}_hashcode'
        dic[hash_key] = value and CustomerStringUtils.to_hashcode(value)

    def _filter_root_module(self, root_module: dict):
        result = {'resources': self._filter_resources(root_module.get('resources', []))}
        module_calls = root_module.get('module_calls', {})
        result['module_calls'] = {module: self._filter_module(module_calls.get(module)) for module in module_calls.keys()}
        return result

    @staticmethod
    def _filter_resources(resources: List[dict]):
        return [{'address': resource.get('address'), 'raw_data': resource.get('raw_data', {})} for resource in resources]

    def _filter_module(self, module: dict):
        filtered_module = {'resources': self._filter_resources(module['module'].get('resources', []))}
        if module.get('module').get('module_calls'):
            filtered_module['module_calls'] = {key: self._filter_module(value) for (key, value) in module.get('module').get('module_calls').items()}
        return {'raw_data': module.get('raw_data'), 'module': filtered_module}

    def run_checkov_checks(self, work_dir: str, checkov_rule_ids: List[str]):
        try:
            results = self.checkov_executor.execute_checkov(work_dir, checkov_rule_ids)
            return TerraformContextResult(True, result=results)
        except Exception as ex:
            logging.exception('error running checkov checks')
            return TerraformContextResult(False, error=str(ex))

    @staticmethod
    def _get_normalized_supported_section(resource_type: str,
                                          services_to_include: Dict[str, SupportedSectionDTO]) -> SupportedSectionDTO:
        common_section: SupportedSectionDTO = services_to_include['common']
        resource_supported_section = services_to_include.get(resource_type)
        if not resource_supported_section:
            return common_section
        resource_supported_section = copy.deepcopy(resource_supported_section)
        resource_known_fields = services_to_include[resource_type].known_fields or KnownFieldsDTO({}, [])
        known_fields = copy.deepcopy(common_section.known_fields)
        known_fields.pass_values.update(resource_known_fields.pass_values)
        known_fields.hash_values.extend(resource_known_fields.hash_values)
        resource_supported_section.known_fields = known_fields
        return resource_supported_section

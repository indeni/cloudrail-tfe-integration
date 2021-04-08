import json
from typing import Tuple, List

from api.dtos.policy_dto import RuleEnforcementModeDTO, PolicyDTO
from api.dtos.rule_info_dto import RuleTypeDTO
from api.dtos.rule_result_dto import RuleResultDTO, ContextEntityDTO, RuleResultStatusDTO
from api.dtos.run_execution_dto import AssessmentJobDTO
from result_formatter.base_formatter import BaseFormatter
from utils.string_utils import StringUtils


class SarifFormatter(BaseFormatter):

    def __init__(self, show_warnings: bool):
        super().__init__()
        self._show_warnings = show_warnings

    def format(self,
               rule_results: List[RuleResultDTO],
               unused_run_exec: AssessmentJobDTO,
               unused_policies: List[PolicyDTO]) -> Tuple[str, str]:
        filtered_results = []
        for rule_result in rule_results:
            if rule_result.status == RuleResultStatusDTO.FAILED and \
                    (rule_result.is_mandate or self._show_warnings):
                filtered_results.append(rule_result)

        result = {
            'version': '2.1.0',
            '$schema': 'https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.4.json',
            'runs': [
                {
                    'tool': {
                        'driver': {
                            'name': 'Indeni Cloudrail',
                            'rules': self._convert_rules_info(filtered_results)
                        }
                    },
                    "results": self._convert_issue_items_to_sarif_results(filtered_results)
                }],
        }
        return json.dumps(result), ''

    @classmethod
    def _convert_rules_info(cls, rule_results: List[RuleResultDTO]):
        rules_info = []
        for rule_result in rule_results:
            rules_info.append({
                'id': rule_result.rule_id,
                'name': rule_result.rule_name,
                'shortDescription': {'text': rule_result.rule_name},
                'fullDescription': {'text': rule_result.rule_description},
                'help': {'text': f'Remediation Steps - Terraform: '
                                 f'{StringUtils.clean_markdown(rule_result.remediation_steps_tf)}'
                                 f'\nRemediation Steps - Cloud Console: '
                                 f'{StringUtils.clean_markdown(rule_result.remediation_steps_console)}'},
                'properties': {'precision': cls._get_rule_precision(rule_result)}
            })
        return rules_info

    @staticmethod
    def _get_rule_precision(rule_result: RuleResultDTO):
        if RuleTypeDTO.CONTEXT_AWARE == rule_result.rule_type:
            return 'very-high'
        else:
            return 'medium'

    @classmethod
    def _convert_issue_items_to_sarif_results(cls, rule_results: List[RuleResultDTO]):
        vulns = []
        for rule_result in rule_results:
            for issue_item in rule_result.issue_items:
                violating_entity = issue_item.violating_entity
                exposed_entity = issue_item.exposed_entity
                location = cls._get_location(violating_entity, exposed_entity)
                if location:
                    vulns.append({
                        "ruleId": rule_result.rule_id,
                        "level": cls._get_level(rule_result.enforcement_mode),
                        "message": {
                            "text": '<{}> is exposing <{}>'.format(violating_entity.get_friendly_name(),
                                                                   exposed_entity.get_friendly_name()),
                            "markdown": '<`{}`> is exposing <`{}`>'.format(violating_entity.get_friendly_name(),
                                                                           exposed_entity.get_friendly_name())
                        },
                        "locations": [cls._get_location(violating_entity, exposed_entity)]
                    })
        return vulns

    @staticmethod
    def _get_location(violating_entity: ContextEntityDTO, exposed_entity: ContextEntityDTO):
        tf_resource_metadata = violating_entity.tf_resource_metadata or exposed_entity.tf_resource_metadata
        if tf_resource_metadata:
            return {
                'physicalLocation': {
                    'artifactLocation': {
                        'uri': tf_resource_metadata.file_name
                    },
                    'region': {
                        'startLine': tf_resource_metadata.start_line,
                        'endLine': tf_resource_metadata.end_line
                    }
                }
            }
        return None

    @staticmethod
    def _get_level(enforcement_mode: RuleEnforcementModeDTO) -> str:
        if enforcement_mode.is_mandate:
            return 'error'
        return 'warning'

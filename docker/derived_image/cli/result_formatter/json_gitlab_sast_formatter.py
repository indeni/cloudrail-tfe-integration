import json
from typing import Tuple, List

from api.dtos.policy_dto import PolicyDTO
from api.dtos.rule_info_dto import RuleSeverityDTO
from api.dtos.rule_result_dto import RuleResultDTO, ContextEntityDTO, RuleResultStatusDTO
from api.dtos.run_execution_dto import AssessmentJobDTO
from result_formatter.base_formatter import BaseFormatter


class JsonGitLabSastFormatter(BaseFormatter):
    def __init__(self, show_warnings: bool):
        super().__init__()
        self._show_warnings = show_warnings

    def format(self, rule_results: List[RuleResultDTO],
               unused_run_exec: AssessmentJobDTO,
               unused_policies: List[PolicyDTO]) -> Tuple[str, str]:
        filtered_results = []
        for rule_result in rule_results:
            if rule_result.status == RuleResultStatusDTO.FAILED and \
                    (rule_result.is_mandate or self._show_warnings):
                filtered_results.append(rule_result)
        result = {
            "version": "2.0",
            "vulnerabilities": self.convert_issue_items_to_githab_vulns(filtered_results)
        }
        return json.dumps(result), ''

    @staticmethod
    def convert_issue_items_to_githab_vulns(rule_results: List[RuleResultDTO]):
        vulns = []
        for rule_result in rule_results:
            for issue_item in rule_result.issue_items:
                violating_entity = issue_item.violating_entity
                exposed_entity = issue_item.exposed_entity
                location = JsonGitLabSastFormatter._get_location(violating_entity, exposed_entity)
                if location:
                    vulns.append({
                        "id": rule_result.id + violating_entity.id + exposed_entity.id,
                        "category": "sast",
                        "name": rule_result.rule_name,
                        "message": rule_result.rule_name + ": <" + violating_entity.get_friendly_name()
                                   + "> is exposing <" + exposed_entity.get_friendly_name() + ">",
                        "description": rule_result.rule_description,
                        "severity": JsonGitLabSastFormatter._get_severity(rule_result.severity),
                        "confidence": "High",
                        "scanner": {
                            "id": "indeni_cloudrail",
                            "name": "Indeni Cloudrail"
                        },
                        "location": location
                    })
        return vulns

    @staticmethod
    def _get_location(violating_entity: ContextEntityDTO, exposed_entity: ContextEntityDTO):
        tf_resource_metadata = violating_entity.tf_resource_metadata or exposed_entity.tf_resource_metadata
        if tf_resource_metadata:
            return {
                "file": tf_resource_metadata.file_name,
                "start_line": tf_resource_metadata.start_line,
                "end_line": tf_resource_metadata.end_line
            }
        return None

    @staticmethod
    def _get_severity(severity_dto: RuleSeverityDTO) -> str:
        if severity_dto == RuleSeverityDTO.MAJOR:
            return 'High'
        return severity_dto.value.title()

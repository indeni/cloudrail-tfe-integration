import json
from typing import List, Tuple

from api.dtos.policy_dto import PolicyDTO
from api.dtos.rule_result_dto import RuleResultDTO
from api.dtos.run_execution_dto import AssessmentJobDTO


class JsonFormatter:
    def __init__(self, show_warnings: bool):
        super().__init__()
        self._show_warnings = show_warnings

    def format(self, rule_results: List[RuleResultDTO],
               unused_run_exec: AssessmentJobDTO,
               unused_policies: List[PolicyDTO]) -> Tuple[str, str]:
        filtered_results = []
        for rule_result in rule_results:
            if rule_result.is_mandate or self._show_warnings:
                filtered_results.append(rule_result)
        return json.dumps(RuleResultDTO.schema().dump(filtered_results, many=True), indent=4, default=lambda o: o.__dict__), ''

from abc import abstractmethod
from typing import List, Dict

from environment_context.environment_context import EnvironmentContext
from environment_context.terraform_resource_finder import TerraformResourceFinder
from rules.base_rule import Issue, BaseRule
from rules.rule_parameters.base_paramerter import ParameterType


class BaseCheckovRule(BaseRule):
    def __init__(self, checkov_rule_id: str) -> None:
        self.checkov_rule_id = checkov_rule_id

    @abstractmethod
    def get_id(self) -> str:
        return self.checkov_rule_id

    def execute(self, env_context: EnvironmentContext, parameters: Dict[ParameterType, any]) -> List[Issue]:
        issues: List[Issue] = []
        rule_results = env_context.checkov_results.get(self.checkov_rule_id, [])
        for rule_result in rule_results:
            resources = TerraformResourceFinder.get_resources(rule_result.file_path,
                                                              rule_result.start_line,
                                                              rule_result.end_line)
            if resources:
                resource = resources[0]
                issues.append(Issue(f"This rule evaluated `{resource.get_friendly_name()}`'s configuration",
                                    resource,
                                    resource))
        return issues

    def get_needed_parameters(self) -> List[ParameterType]:
        return []

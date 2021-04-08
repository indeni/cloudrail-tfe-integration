import os
from typing import List, Tuple

from junit_xml import TestSuite, TestCase

from api.dtos.policy_dto import PolicyDTO
from api.dtos.rule_result_dto import RuleResultDTO, RuleResultStatusDTO

# JUNIT -  https://github.com/kyrus/python-junit-xml
from api.dtos.run_execution_dto import AssessmentJobDTO
from result_formatter.base_formatter import BaseFormatter
from utils.string_utils import StringUtils


class JunitFormatter(BaseFormatter):
    def __init__(self, api_key: str, directory: str, tf_plan: str, junit_package_name_prefix: str):
        super().__init__()
        self.junit_package_name_prefix: str = junit_package_name_prefix
        self.properties = {
            'api_key': api_key,
            'directory': os.path.relpath(directory),
            'plan_path': os.path.relpath(tf_plan),
            'output': 'junit'
        }

    def format(self, rule_results: List[RuleResultDTO],
               run_exec: AssessmentJobDTO,
               unused_policies: List[PolicyDTO]) -> Tuple[str, str]:
        failures: List[RuleResultDTO] = []
        successes: List[RuleResultDTO] = []
        for rule_result in rule_results:
            if rule_result.is_mandate:
                if rule_result.status == RuleResultStatusDTO.FAILED:
                    failures.append(rule_result)
                elif rule_result.status == RuleResultStatusDTO.SUCCESS:
                    successes.append(rule_result)

        test_suites = []
        suite_id = 1

        for success in successes:
            test_cases = [TestCase(name=success.rule_name, classname=self.get_class_name(success), status="SUCCESSFUL")]
            test_suites.append(TestSuite(suite_id, test_cases, properties=self.properties))
            suite_id += 1
        for failure in failures:
            test_cases = []
            class_name = self.get_class_name(failure)
            for item in failure.issue_items:
                test_case = TestCase(name=item.exposed_entity.get_friendly_name(), classname=class_name, status="FAILED")
                message = self._format_issue_item(item)
                message.insert(0, f'Remediation Steps - Cloud Console: '
                                  f'{StringUtils.clean_markdown(failure.remediation_steps_console)}')
                message.insert(0, f'Remediation Steps - Terraform: '
                                  f'{StringUtils.clean_markdown(failure.remediation_steps_tf)}')
                message.insert(0, f'Description: {failure.rule_description}')
                if self._issue_item_contains_pseudo_entity(item):
                    message.extend(self._pseudo_message)

                test_case.add_failure_info(output='\n'.join(message))
                test_cases.append(test_case)

            test_suites.append(TestSuite(suite_id, test_cases, properties=self.properties))
            suite_id += 1

        unknown_block_message = self._get_unknown_block_message(run_exec.tf_unknown_blocks)

        return TestSuite.to_xml_string(test_suites), '\n'.join(unknown_block_message)

    def get_class_name(self, rule_result: RuleResultDTO) -> str:
        layer = rule_result.security_layer.value.title()
        return f'{self.junit_package_name_prefix}{layer}.{rule_result.rule_id}'

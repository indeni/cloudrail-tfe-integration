import copy
import logging
from dataclasses import dataclass
from typing import List, Dict

import backoff
from checkov.common.runners.runner_registry import RunnerRegistry
from checkov.runner_filter import RunnerFilter
from checkov.terraform.runner import Runner as tf_runner

@dataclass
class CheckovResult:
    check_id: str
    file_path: str
    resource: str
    start_line: int
    end_line: int

    @staticmethod
    def from_dict(dic: dict):
        return CheckovResult(dic['check_id'], dic['file_path'], dic['resource'], dic['start_line'], dic['end_line'])


class CheckovExecutor:

    def execute_checkov(self, working_dir: str, checkov_rule_ids: List[str]) -> Dict[str, List[CheckovResult]]:
        raw_results = self._safe_execute_checkov(working_dir, checkov_rule_ids)

        results = {}
        for raw_result in raw_results:
            for failed_check in raw_result.failed_checks:
                if not failed_check.file_line_range:
                    continue
                check_id = failed_check.check_id
                checkov_result = CheckovResult(check_id=failed_check.check_id,
                                               file_path=failed_check.file_path,
                                               resource=failed_check.resource,
                                               start_line=failed_check.file_line_range[0],
                                               end_line=failed_check.file_line_range[1])
                logging.debug('found failed checkov result: {}'.format(vars(checkov_result)))
                if check_id not in results:
                    results[check_id] = []
                results[check_id].append(checkov_result)

        return results

    @staticmethod
    @backoff.on_exception(backoff.expo, Exception, max_time=60)
    def _safe_execute_checkov(working_dir: str, checkov_rule_ids: List[str]) -> list:
        checkov_rule_ids = copy.deepcopy(checkov_rule_ids)
        runner_registry = RunnerRegistry('', RunnerFilter(checks=checkov_rule_ids), tf_runner())
        raw_results = runner_registry.run(working_dir)
        return raw_results

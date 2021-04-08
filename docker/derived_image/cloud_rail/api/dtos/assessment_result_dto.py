from dataclasses import dataclass
from enum import Enum
from typing import List

from dataclasses_json import DataClassJsonMixin

from api.dtos.associated_account_data_dto import AssociatedAccountDataDTO
from api.dtos.associated_policy_dto import AssociatedPolicyDTO
from api.dtos.run_execution_dto import RunOriginDTO


class AssessmentResultTypeDTO(str, Enum):
    PASSED = 'Passed'
    PASSED_WITH_WARNINGS = 'Passed with warnings'
    FAILED_DUE_TO_VIOLATIONS = 'Failed due to violations'


@dataclass
class ResultsSummaryDTO(DataClassJsonMixin):
    assessment_result_type: AssessmentResultTypeDTO = AssessmentResultTypeDTO.PASSED
    evaluated_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    skipped_rules: int = 0
    ignored_rules: int = 0


@dataclass
class AssessmentResultDTO(DataClassJsonMixin):
    id: str
    account: AssociatedAccountDataDTO
    created_at: str
    origin: RunOriginDTO
    build_link: str
    execution_source_identifier: str
    results_summary: ResultsSummaryDTO
    associated_policies: List[AssociatedPolicyDTO]

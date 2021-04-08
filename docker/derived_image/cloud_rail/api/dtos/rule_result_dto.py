from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin

from api.dtos.associated_account_data_dto import AssociatedAccountDataDTO
from api.dtos.datetime_field import datetime_field
from api.dtos.policy_dto import RuleEnforcementModeDTO
from api.dtos.rule_info_dto import RuleSeverityDTO, ResourceTypeDTO, SecurityLayerDTO, RuleTypeDTO
from api.dtos.run_execution_dto import RunOriginDTO


class IssueSeverityDTO(str, Enum):
    WARNING = 'warning'


class RuleResultStatusDTO(str, Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    SKIPPED = 'skipped'
    IGNORED = 'ignored'


@dataclass
class TerraformResourceMetadataDTO(DataClassJsonMixin):
    address: str
    file_name: str
    start_line: int
    end_line: int
    module_metadata: Optional['TerraformResourceMetadataDTO'] = None
    id: Optional[str] = None


@dataclass
class ContextEntityDTO(DataClassJsonMixin):
    id: str
    name: Optional[str]
    cloud_arn: Optional[str]
    type: str
    is_pseudo: bool
    managed_by_tf: Optional[bool] = None
    tf_address: Optional[str] = None
    cloud_resource_url: Optional[str] = None
    tf_resource_metadata: Optional[TerraformResourceMetadataDTO] = None
    cloud_id: Optional[str] = None
    created_at: datetime = datetime_field()
    friendly_name: str = None

    def get_friendly_name(self) -> str:
        return self.tf_address or self.name or self.cloud_id or self.cloud_arn


@dataclass
class IssueItemDTO(DataClassJsonMixin):
    evidence: str
    exposed_entity: Optional[ContextEntityDTO] = None
    violating_entity: Optional[ContextEntityDTO] = None


@dataclass
class RuleResultDTO(DataClassJsonMixin):
    # Rule result data:
    id: str
    status: RuleResultStatusDTO
    issue_items: List[IssueItemDTO]
    enforcement_mode: RuleEnforcementModeDTO
    created_at: str
    # rule meta data
    rule_id: str
    rule_name: str
    rule_description: str
    rule_logic: str
    severity: RuleSeverityDTO
    categories: List[str]
    rule_type: RuleTypeDTO
    security_layer: SecurityLayerDTO
    resource_types: List[ResourceTypeDTO]
    remediation_steps_tf: str
    remediation_steps_console: str
    # account
    account: AssociatedAccountDataDTO
    # assessment data
    assessment_id: str
    origin: RunOriginDTO
    build_link: str
    execution_source_identifier: str
    # policy data
    policy_id: Optional[str]
    policy_name: Optional[str]

    @property
    def is_mandate(self):
        return self.enforcement_mode.is_mandate

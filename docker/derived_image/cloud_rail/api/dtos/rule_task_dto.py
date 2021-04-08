from dataclasses import dataclass
from typing import List

from dataclasses_json import DataClassJsonMixin

from api.dtos.associated_account_data_dto import AssociatedAccountDataDTO
from api.dtos.rule_info_dto import RuleSeverityDTO, RuleTypeDTO, SecurityLayerDTO, ResourceTypeDTO


@dataclass
class RuleTaskDTO(DataClassJsonMixin):
    rule_id: str
    rule_name: str
    description: str
    categories: List[str]
    rule_type: RuleTypeDTO
    security_layer: SecurityLayerDTO
    resource_types: List[ResourceTypeDTO]
    severity: RuleSeverityDTO
    logic: str
    remediation_steps_tf: str
    remediation_steps_console: str
    last_validation: str
    accounts: List[AssociatedAccountDataDTO]

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin

from api.dtos.associated_account_data_dto import AssociatedAccountDataDTO
from environment_context.common.input_validator import InputValidator


class RuleEnforcementModeDTO(str, Enum):
    ADVISE = 'advise'
    MANDATE_ALL_RESOURCES = 'mandate'
    MANDATE_NEW_RESOURCES = 'mandate_new_resources'
    IGNORE = 'ignore'

    @property
    def is_mandate(self):
        return self in (RuleEnforcementModeDTO.MANDATE_NEW_RESOURCES, RuleEnforcementModeDTO.MANDATE_ALL_RESOURCES)


@dataclass
class PolicyRuleDTO(DataClassJsonMixin):
    rule_id: str
    enforcement_mode: RuleEnforcementModeDTO

    def __post_init__(self):
        InputValidator.validate_allowed_chars(self.rule_id)


@dataclass
class PolicyRuleBulkAddDataDTO(DataClassJsonMixin):
    id: str
    policy_rules: List[PolicyRuleDTO]

    def __post_init__(self):
        InputValidator.validate_uuid(self.id)


@dataclass
class PolicyAddDTO(DataClassJsonMixin):
    name: str
    description: str
    policy_rules: List[PolicyRuleDTO] = field(default_factory=list)
    account_config_ids: List[str] = field(default_factory=list)
    active: bool = True

    def __post_init__(self):
        InputValidator.validate_allowed_chars(self.name)
        InputValidator.validate_allowed_chars(self.description)
        for account_config_id in self.account_config_ids:
            InputValidator.validate_uuid(account_config_id)


@dataclass
class PolicyDTO(DataClassJsonMixin):
    name: str
    description: str
    policy_rules: List[PolicyRuleDTO] = field(default_factory=list)
    accounts: List[AssociatedAccountDataDTO] = field(default_factory=list)
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    active: bool = True
    is_deleted: bool = False


@dataclass
class PolicyUpdateDTO(DataClassJsonMixin):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    account_config_ids: Optional[List[str]] = None

    def __post_init__(self):
        InputValidator.validate_allowed_chars(self.name, True)
        InputValidator.validate_allowed_chars(self.description, True)
        if self.account_config_ids:
            for account_config_id in self.account_config_ids:
                InputValidator.validate_uuid(account_config_id)



@dataclass
class PolicyRuleUpdateDTO(DataClassJsonMixin):
    enforcement_mode: RuleEnforcementModeDTO

from enum import Enum


class RuleTaskSortColumnDTO(str, Enum):
    RULE_NAME = 'rule_name'
    SEVERITY = 'severity'
    LAST_VALIDATION = 'last_validation'


class RunExecutionSortColumnDTO(str, Enum):
    CREATED_AT = 'created_at'
    ACCOUNT_NAME = 'account_name'


class AccountConfigSortColumnDTO(str, Enum):
    LAST_COLLECTED_AT = 'last_collected_at'
    NAME = 'name'
    STATUS = 'status'


class PolicySortColumnDTO(str, Enum):
    NAME = 'name'
    UPDATED_AT = 'updated_at'
    POLICY_RULES = 'policy_rules'
    ACCOUNTS = 'accounts'

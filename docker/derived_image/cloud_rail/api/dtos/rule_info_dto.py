from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin

from api.dtos.associated_policy_dto import AssociatedPolicyDTO
from api.dtos.rule_execlusion_dto import RuleExclusionDTO


class RuleSeverityDTO(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    MAJOR = 'major'

class RuleTypeDTO(str, Enum):
    NON_CONTEXT_AWARE = 'non_context_aware'
    CONTEXT_AWARE = 'context_aware'


class SecurityLayerDTO(str, Enum):
    IAM = 'iam'
    ENCRYPTION = 'encryption'
    NETWORKING = 'networking'
    LOGGING = 'logging'
    CODE = 'code'
    DISASTER_RECOVERY = 'disaster_recovery'
    STORAGE = 'storage'
    TAGGING = 'tagging'


class ResourceTypeDTO(str, Enum):
    ALL = 'all'
    KUBERNETES = 'kubernetes'
    COMPUTE = 'compute'
    IAM = 'iam'
    FIREWALL = 'firewall'
    STORAGE = 'storage'
    KEY_MGMT = 'key_mgmt'
    NETWORK = 'network'
    DATABASE = 'database'
    CLOUDFRONT = 'cloudfront'
    CONTENT_DELIVERY = 'content_delivery'
    SERVICE_ENDPOINT = 'service_endpoint'
    CODE = 'code'
    LOGGING = 'logging'
    QUEUING = 'queuing'
    NOTIFICATION = 'notification'
    STREAMING = 'streaming'


@dataclass
class RuleInfoDTO(DataClassJsonMixin):
    id: str
    name: str
    description: str
    severity: RuleSeverityDTO
    categories: List[str]
    rule_type: RuleTypeDTO
    security_layer: SecurityLayerDTO
    resource_types: List[ResourceTypeDTO]
    logic: str
    remediation_steps_tf: str
    remediation_steps_console: str
    active: bool
    associated_policies: List[AssociatedPolicyDTO]
    rule_exclusion: RuleExclusionDTO


@dataclass
class RuleUpdateDTO(DataClassJsonMixin):
    active: Optional[bool] = None
    rule_exclusion: Optional[RuleExclusionDTO] = None


@dataclass
class RuleBulkUpdateDTO(DataClassJsonMixin):
    id: str
    active: Optional[bool]

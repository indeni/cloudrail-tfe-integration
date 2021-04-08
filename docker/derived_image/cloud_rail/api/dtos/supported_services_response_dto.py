from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from dataclasses_json import DataClassJsonMixin


class FieldActionDTO(str, Enum):
    SKIP = 'skip'
    PASS = 'pass'
    HASH = 'hash'


@dataclass
class KnownFieldsDTO(DataClassJsonMixin):
    pass_values: Dict[str, Optional['SupportedSectionDTO']]
    hash_values: List[str]


@dataclass
class SupportedSectionDTO(DataClassJsonMixin):
    known_fields: Optional[KnownFieldsDTO]
    unknown_fields_action: FieldActionDTO


@dataclass
class SupportedAwsServicesResponseDTO(DataClassJsonMixin):
    supported_aws_services: Dict[str, SupportedSectionDTO]


@dataclass
class SupportedCheckovServicesResponseDTO(DataClassJsonMixin):
    supported_checkov_services: List[str]

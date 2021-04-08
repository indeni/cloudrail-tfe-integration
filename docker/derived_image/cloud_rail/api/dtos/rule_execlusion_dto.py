from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import DataClassJsonMixin


class CompareOperatorDTO(str, Enum):
    EQUAL = 'equal'
    CONTAINS = 'contains'
    ANY = 'any'


@dataclass
class RuleExclusionDTO(DataClassJsonMixin):
    key: str
    value: Optional[str]
    compare_operator: CompareOperatorDTO

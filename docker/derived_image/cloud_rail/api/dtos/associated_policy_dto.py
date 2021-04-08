from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin


@dataclass
class AssociatedPolicyDTO(DataClassJsonMixin):
    id: str
    name: str

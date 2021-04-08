from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


@dataclass
class ConnectionTestDTO(DataClassJsonMixin):
    connection_test_passed: bool
    account_id: str

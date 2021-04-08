from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class EnvironmentContextResultDTO(DataClassJsonMixin):
    is_success: bool
    context: Optional[str] = None
    error: Optional[str] = None

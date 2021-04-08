import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from environment_context.common.input_validator import InputValidator


class BlockType(str, Enum):
    DATASOURCE = 'datasource'


@dataclass
class UnknownBlock:
    block_type: BlockType
    block_address: str


class TerraformActionType(str, Enum):
    NO_OP = 'no-op'
    CREATE = 'create'
    DELETE = 'delete'
    UPDATE = 'update'
    READ = 'read'


@dataclass
class TerraformRawData:
    file_name: str
    start_line: int
    end_line: int


@dataclass
class TerraformResourceMetadata:
    address: str
    file_name: str
    start_line: int
    end_line: int
    module_metadata: Optional['TerraformResourceMetadata'] = None
    id: Optional[str] = None
    resource_type: Optional[str] = None
    run_execution_id: str = None

    def __post_init__(self):
        self.id = self.id or str(uuid.uuid4())

    def validate(self):
        InputValidator.validate_allowed_chars(self.address, True)
        InputValidator.validate_allowed_chars(self.file_name, True)
        InputValidator.validate_int(self.start_line, True)
        InputValidator.validate_int(self.end_line, True)
        InputValidator.validate_allowed_chars(self.resource_type, True)
        InputValidator.validate_uuid(self.id, True)
        if self.module_metadata:
            self.module_metadata.validate()


@dataclass
class TerraformState:
    address: str
    action: TerraformActionType
    resource_metadata: Optional[TerraformResourceMetadata]
    is_new: bool

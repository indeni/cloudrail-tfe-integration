from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from environment_context.common.input_validator import InputValidator


class AccountStatusDTO(str, Enum):
    CONNECTING = 'connecting'
    INITIAL_ENVIRONMENT_MAPPING = 'initial environment mapping'
    READY = 'ready'
    ERROR = 'error'


class CloudProviderDTO(str, Enum):
    AMAZON_WEB_SERVICES = 'Amazon Web Services'


@dataclass
class AccountConfigDTO(DataClassJsonMixin):
    name: str
    cloud_account_id: str
    interval_seconds: Optional[int] = None
    external_id: Optional[str] = None
    role_name: Optional[str] = None
    created_at: str = None
    status: AccountStatusDTO = AccountStatusDTO.CONNECTING
    id: str = None
    last_collected_at: str = None
    cloud_provider: CloudProviderDTO = None
    customer_id: str = None


@dataclass
class AccountConfigAddDTO(DataClassJsonMixin):
    name: str
    cloud_account_id: str
    interval_seconds: Optional[int] = None

    def __post_init__(self):
        InputValidator.validate_allowed_chars(self.name)
        InputValidator.validate_cloud_account_id(self.cloud_account_id)


@dataclass
class AccountConfigUpdateDTO(DataClassJsonMixin):
    name: str

    def __post_init__(self):
        InputValidator.validate_allowed_chars(self.name)

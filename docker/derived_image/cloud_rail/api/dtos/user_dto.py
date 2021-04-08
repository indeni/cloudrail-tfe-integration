from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from environment_context.common.input_validator import InputValidator


class UserStatusDTO(str, Enum):
    UNCONFIRMED = 'unconfirmed'
    CONFIRMED = 'confirmed'
    ARCHIVED = 'archived'
    COMPROMISED = 'compromised'
    UNKNOWN = 'unknown'
    RESET_REQUIRED = 'reset_required'
    FORCE_CHANGE_PASSWORD = 'force_change_password'

@dataclass
class UserDTO(DataClassJsonMixin):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    customer_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: Optional[UserStatusDTO] = None


@dataclass
class UserUpdateDTO(DataClassJsonMixin):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def __post_init__(self):
        InputValidator.validate_allowed_chars(self.first_name, True)
        InputValidator.validate_allowed_chars(self.last_name, True)


@dataclass
class UserRegisterDTO(DataClassJsonMixin):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def __post_init__(self):
        InputValidator.validate_email(self.email)
        InputValidator.validate_allowed_chars(self.first_name)
        InputValidator.validate_allowed_chars(self.last_name)


@dataclass
class UserRegisterWithInvitationDTO(DataClassJsonMixin):
    email: str
    temporary_password: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def __post_init__(self):
        InputValidator.validate_email(self.email)
        InputValidator.validate_allowed_chars(self.first_name)
        InputValidator.validate_allowed_chars(self.last_name)


@dataclass
class UserInviteDTO(DataClassJsonMixin):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def __post_init__(self):
        InputValidator.validate_email(self.email)
        InputValidator.validate_allowed_chars(self.first_name, True)
        InputValidator.validate_allowed_chars(self.last_name, True)


@dataclass
class UserUnregisterDTO(DataClassJsonMixin):
    email: str
    password: str

    def __post_init__(self):
        InputValidator.validate_email(self.email)


@dataclass
class UserLoginDTO(DataClassJsonMixin):
    email: str
    password: str

    def __post_init__(self):
        InputValidator.validate_email(self.email)


@dataclass
class UserResetPasswordDTO(DataClassJsonMixin):
    email: str
    password: str
    confirmation_code: str

    def __post_init__(self):
        InputValidator.validate_email(self.email)
        self.confirmation_code = self.confirmation_code or ''
        self.confirmation_code = self.confirmation_code.strip()
        InputValidator.validate_confirmation_code(self.confirmation_code)


@dataclass
class UserResetPasswordRequestDTO(DataClassJsonMixin):
    email: str

    def __post_init__(self):
        InputValidator.validate_email(self.email)


@dataclass
class UserChangePasswordDTO(DataClassJsonMixin):
    password: str
    new_password: str


@dataclass
class UserWithTokenDTO(UserDTO):
    id_token: str = None
    access_token: str = None
    expires_in: int = None
    refresh_token: str = None


@dataclass
class ApiKeyDTO(DataClassJsonMixin):
    api_key: str


@dataclass
class UserInvitationSummaryDTO(DataClassJsonMixin):
    email: str
    invitation_sent: bool
    error: Optional[str] = None


@dataclass
class UserResetPasswordRequestSummaryDTO(DataClassJsonMixin):
    email: str
    confirmation_code_sent: bool

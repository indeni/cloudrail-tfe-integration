from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


@dataclass
class BaseCloudrailResponse:
    success: bool


@dataclass
class CloudrailErrorResponse(BaseCloudrailResponse):
    message: str = ''
    success: bool = False


@dataclass
class CloudrailSuccessJsonResponse(BaseCloudrailResponse):
    data: DataClassJsonMixin = None
    success: bool = True

@dataclass
class CloudrailSuccessDataResponse(BaseCloudrailResponse):
    data: str = None
    success: bool = True

from dataclasses import dataclass

@dataclass
class ServiceResponse:
    success: bool
    message: str


class ServiceResponseFactory:
    @staticmethod
    def success(message: str) -> ServiceResponse:
        return ServiceResponse(True, message)

    @staticmethod
    def failed(message: str) -> ServiceResponse:
        return ServiceResponse(False, message)

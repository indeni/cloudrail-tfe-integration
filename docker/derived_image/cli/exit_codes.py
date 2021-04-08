from enum import Enum


class ExitCode(Enum):
    OK = 0
    MANDATORY_RULES_FAILED = 1
    BACKEND_ERROR = 2
    INVALID_INPUT = 3
    CONTEXT_ERROR = 4
    USER_TERMINATION = 5
    TIMEOUT = 6
    CLI_ERROR = 7

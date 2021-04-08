from dataclasses import dataclass


@dataclass
class CheckovResult:
    check_id: str
    file_path: str
    resource: str
    start_line: int
    end_line: int

from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin

# pylint:disable=invalid-name
@dataclass
class AssessmentsStatisticsDTO:
    total: int = 0
    ci: int = 0
    workstation: int = 0

@dataclass
class CustomerStatisticsDTO(DataClassJsonMixin):
    accounts: int = 0
    assessments: AssessmentsStatisticsDTO = AssessmentsStatisticsDTO()

@dataclass
class CustomerDTO(DataClassJsonMixin):
    id: str
    external_id: str
    role_name: str
    created_at: str
    cloudformation_url: str
    cloudformation_template_url: str
    statistics: CustomerStatisticsDTO = CustomerStatisticsDTO()

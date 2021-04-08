from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin

from api.dtos.account_config_dto import CloudProviderDTO


@dataclass
class AssociatedAccountDataDTO(DataClassJsonMixin):
    id: str
    cloud_account_id: str
    name: str
    cloud_provider: CloudProviderDTO

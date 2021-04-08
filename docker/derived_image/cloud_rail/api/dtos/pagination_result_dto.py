from dataclasses import dataclass
from typing import List, TypeVar, Generic

from dataclasses_json import DataClassJsonMixin

ResultTypeDTO = TypeVar('ResultTypeDto')


@dataclass
class PaginationResultDTO(DataClassJsonMixin, Generic[ResultTypeDTO]):
    page_number: int
    items_per_page: int
    total_pages: int
    total_items: int
    page_results: List[ResultTypeDTO]

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict

from dataclasses_json import DataClassJsonMixin

from api.dtos.datetime_field import datetime_field


class RunOriginDTO(str, Enum):
    WORKSTATION = 'workstation'
    CI = 'ci'


class RunStatusDTO(str, Enum):
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'


class StepFunctionStepDTO(str, Enum):
    COLLECT = 'collect'
    WAIT_FOR_CONTEXT = 'wait_for_context'
    WAIT_FOR_COLLECT = 'wait_for_collect'
    PROCESS_STARTED = 'process_started'
    PROCESS_RUNNING_TF_SHOW = 'process_running_tf_show'
    PROCESS_BUILDING_ENV_CONTEXT = 'process_building_env_context'
    RUN_RULES = 'run_rules'
    SAVING_RESULTS = 'saving_results'
    UNKNOWN = 'unknown'

    @staticmethod
    def get_steps():
        return [StepFunctionStepDTO.COLLECT,
                StepFunctionStepDTO.WAIT_FOR_CONTEXT,
                StepFunctionStepDTO.WAIT_FOR_COLLECT,
                StepFunctionStepDTO.PROCESS_STARTED,
                StepFunctionStepDTO.PROCESS_RUNNING_TF_SHOW,
                StepFunctionStepDTO.PROCESS_BUILDING_ENV_CONTEXT,
                StepFunctionStepDTO.RUN_RULES,
                StepFunctionStepDTO.SAVING_RESULTS]


class RunTypeDTO(str, Enum):
    COLLECT = 'collect'
    COLLECT_PROCESS_TEST = 'collect_process_test'
    PROCESS_TEST = 'process_test'


class BlockTypeDTO(str, Enum):
    DATASOURCE = 'datasource'


@dataclass
class UnknownBlockDTO:
    block_type: BlockTypeDTO
    block_address: str


@dataclass
class AssessmentJobDTO(DataClassJsonMixin):
    id: str
    account_config_id: str
    customer_id: str
    run_status: RunStatusDTO
    run_type: RunTypeDTO = None
    last_step: Optional[StepFunctionStepDTO] = None
    error_message: Optional[str] = None
    created_at: datetime = datetime_field()
    tf_unknown_blocks: List[UnknownBlockDTO] = field(default_factory=list)
    origin: Optional[RunOriginDTO] = None
    build_link: Optional[str] = None
    execution_source_identifier: Optional[str] = None
    collect_job_id: Optional[str] = None
    feature_flags: Dict[str, bool] = field(default_factory=dict)

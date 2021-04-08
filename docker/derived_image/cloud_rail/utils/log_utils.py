import functools
import logging
import re
from enum import Enum
from typing import Dict


class SensitiveFilter(logging.Filter):
    def filter(self, record):
        return not re.search('api-key|api_key|password|role_name|external_id|apiKey', record.getMessage())


class LogUtils(int, Enum):
    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_log_level_aliases() -> Dict[str, int]:
        return {
            'CRITICAL': logging.CRITICAL,
            'FATAL': logging.FATAL,
            'ERROR': logging.ERROR,
            'WARN': logging.WARNING,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
            'NOTSET': logging.NOTSET
        }

    @staticmethod
    def init_logger(log_level=logging.INFO):
        logger = logging.getLogger()
        logger.setLevel(log_level)
        logger.addFilter(SensitiveFilter())

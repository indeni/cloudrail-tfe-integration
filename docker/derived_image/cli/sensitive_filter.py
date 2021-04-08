import logging
import re


class SensitiveFilter(logging.Filter):
    def filter(self, record):
        return not re.search('api-key|api_key|password|role_name|external_id', record.getMessage())

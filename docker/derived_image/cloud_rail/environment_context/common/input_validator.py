import inspect
import logging
import os
import re
from typing import Optional

from utils.log_utils import LogUtils


class ValidationException(Exception):
    pass


class InputValidator:

    @classmethod
    def validate_cloud_account_id(cls, value: str, error_message='invalid cloud account id'):
        cls._validate_regex(value, r'^[0-9]{12}$', error_message)

    @classmethod
    def validate_email(cls, value: str, error_message='Invalid email format'):
        cls._validate_regex(value,
                            r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
                            error_message)

    @classmethod
    def validate_confirmation_code(cls, value: str, error_message='Invalid confirmation code format'):
        cls._validate_regex(value,
                            r'^[\S]+$',
                            error_message)

    @classmethod
    def validate_allowed_chars(cls, value: str, allow_none: bool = False, error_message='Invalid characters (allowed A-Za-z0-9-_#:\'".,`~/()[]*{})'):
        cls._validate_regex(value,
                            r'^[A-Za-z0-9-_#:\'".,\s`~/()\[\]*{}\$]+$',
                            error_message,
                            allow_none)

    @classmethod
    def validate_html_link(cls,
                           value: str,
                           error_message: str = 'Invalid http link format',
                           allow_none: bool = False):
        cls._validate_regex(value,
                            r'^https?:\/\/[-a-zA-Z0-9()@:%_\+.~#?&\/=]+$',
                            error_message,
                            allow_none)

    @classmethod
    def validate_log_level(cls, value: str):
        known_log_levels = LogUtils.get_log_level_aliases().keys()
        if value.upper() not in known_log_levels:
            known_log_levels_as_str = ', '.join(known_log_levels)
            error_message = f'Unsupported log level provided, options are: {known_log_levels_as_str}.'
            raise ValidationException(error_message)

    @classmethod
    def validate_api_key(cls, value: str, error_message: str = 'Invalid api key format'):
        cls._validate_regex(value,
                            r'^[0-9a-zA-Z-_]{43}$',
                            error_message,
                            False)

    @classmethod
    def validate_uuid(cls, value: str, allow_none: bool = False, error_message='Invalid uuid format'):
        cls._validate_regex(value, r'^[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}$',
                            error_message,
                            allow_none)

    @classmethod
    def validate_int(cls, value: str, allow_none: bool = False, error_message='Invalid int format'):
        cls._validate_regex(value, r'^[0-9]+$',
                            error_message,
                            allow_none)

    @classmethod
    def _validate_regex(cls,
                        value: str,
                        regex: str,
                        error_message: str,
                        allow_none: bool = False):

        key = cls._find_field_key(value)
        key_message = ' for field {}'.format(key) if key else ''
        if not value and not allow_none:
            raise ValidationException('{}{}. Value cannot be empty.'.format(error_message, key_message))
        if not value:
            return
        result = re.match(regex, str(value))
        if not result:
            raise ValidationException('{}{}: {}.'.format(error_message, key_message, value))

    @staticmethod
    def _find_field_key(value: str) -> Optional[str]:
        current_file = os.path.abspath(__file__)
        stack = inspect.stack()
        matched_info = None
        for info in stack:
            # search for the first file which is not the current one.
            if os.path.abspath(info.filename) != os.path.abspath(current_file):
                matched_info = info
                break
        if not matched_info:
            logging.warning('Input validator cant find field key of value: {}'.format(value))
            return None
        code_context = matched_info.code_context
        match = re.search(r'\.validate_.+\(([^,]*)(?:,.*)?\)', str(code_context))
        if not match:
            return None
        validate_input = match.group(1)
        normalized_input = validate_input.split('.')[-1]
        return normalized_input

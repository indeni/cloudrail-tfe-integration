import os
import logging
from enum import Enum
from pathlib import Path
import yaml

from environment_context.common.input_validator import ValidationException, InputValidator

logger = logging.getLogger('cli')


class CliConfigurationKey(str, Enum):
    API_KEY = 'api_key'
    ENDPOINT = 'endpoint'
    LOG_LEVEL = 'log_level'


class CliConfiguration:

    def __init__(self, path: str = None):
        path = path or os.getenv('CLOUDRAIL_CONFIG_PATH', str(Path.home()) + '/.cloudrail/config')
        basename = os.path.dirname(path)
        Path(basename).mkdir(parents=True, exist_ok=True)
        self.configuration_file_path = path
        if not os.path.isfile(self.configuration_file_path):
            self._write_config_file({}, True)
        else:
            self._convert_existing_config_file()

    def get(self, key: CliConfigurationKey, default: str = None):
        self._validate_config_key(key)
        config = self._read_config_file()
        return config.get(key, default)

    def set(self, key: CliConfigurationKey, value: str):
        self._validate_config_key(key)
        key = CliConfigurationKey(key)
        self._validate_config_value(key, value)
        config = self._read_config_file()
        config[key.value] = value
        self._write_config_file(config)

    def unset(self, key: CliConfigurationKey):
        self._validate_config_key(key)
        key = CliConfigurationKey(key)
        config = self._read_config_file()
        if key.value in config:
            del config[key.value]
            self._write_config_file(config)

    def get_all(self):
        return self._read_config_file()

    def clear_all(self):
        self._write_config_file({})

    def _convert_existing_config_file(self):
        new_config = {}
        old_config = self._read_config_file()
        allowed_config_keys = [config_pair.value for config_pair in CliConfigurationKey]
        for config_key in old_config:
            if config_key in allowed_config_keys:
                new_config[config_key] = old_config[config_key]
            if config_key == 'service_endpoint':
                new_config[CliConfigurationKey.ENDPOINT.value] = old_config[config_key]
        self._write_config_file(new_config)

    @staticmethod
    def _validate_config_key(config_key: str):
        allowed_config_keys = [config_pair.value for config_pair in CliConfigurationKey]
        if config_key not in allowed_config_keys:
            raise ValidationException(f'Unknown config key \'{config_key}\'. Supported keys are: {str(allowed_config_keys)}.')

    @staticmethod
    def _validate_config_value(config_key: str, config_value: str):
        if config_key == CliConfigurationKey.API_KEY:
            InputValidator.validate_api_key(config_value,
                                            error_message='The API key entered does not match the format required. '
                                                          'Check to see it was copied correctly')
        elif config_key == CliConfigurationKey.ENDPOINT:
            InputValidator.validate_html_link(config_value,
                                              error_message='The API endpoint provided does not match the format required. '
                                                            'Check to see it was copied correctly')
        elif config_key == CliConfigurationKey.LOG_LEVEL:
            InputValidator.validate_log_level(config_value)

    def _read_config_file(self) -> dict:
        try:
            if os.path.isfile(self.configuration_file_path):
                with open(self.configuration_file_path, 'r+') as file:
                    config = yaml.safe_load(file)
                    if not config:
                        config = {}
            else:
                config = {}
            return config
        except Exception as ex:
            msg = 'Error while reading config file.'
            logging.exception('{} Error is:\n{}'.format(msg, str(ex)))
            raise Exception(msg)

    def _write_config_file(self, config: dict, chmod: bool = False) -> dict:
        try:
            with open(self.configuration_file_path, 'w+') as file:
                yaml.dump(config, file)
            if chmod:
                os.chmod(self.configuration_file_path, 0o600)
        except Exception as ex:
            msg = 'Error while writing config file.'
            logging.exception('{} Error is:\n{}'.format(msg, str(ex)))
            raise Exception(msg)

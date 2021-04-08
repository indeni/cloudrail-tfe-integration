import json
import logging
import os
import re
import zipfile
from pathlib import Path
from typing import Optional

from exceptions import TerraformShowException
import python_terraform
from semantic_version import SimpleSpec, Version
from environment_context.common.terraform_service.terraform_raw_data_explorer import TerraformRawDataExplorer


class TerraformPlanConverter:

    def convert_to_json(self,
                        terraform_plan_path: str,
                        terraform_env_path: str,
                        working_dir: str) -> str:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        TerraformRawDataExplorer.update_working_dir(terraform_env_path)
        plan_folder = self._uncompress_plan(terraform_plan_path, working_dir)
        state_path = self._get_state_file(plan_folder)
        tf_version = self._extract_tf_version(state_path)
        self._validate_terraform_version(tf_version)
        tf_path = self._prepare_terraform(current_dir, tf_version)
        plugins_path = os.path.join(current_dir, 'plugins')
        target_plugins_path = os.getenv('TF_PLUGINS_PATH', str(Path.home()) + '/terraform_plugins')
        override_data_dir_path = self._create_override_data_dir_path(terraform_env_path, working_dir)
        output_path = os.path.join(working_dir, 'output.json')
        self._prepare_plugins(plugins_path, target_plugins_path)
        json_output = self._run_terraform_show(tf_path,
                                               terraform_plan_path,
                                               terraform_env_path,
                                               target_plugins_path,
                                               override_data_dir_path,
                                               output_path)
        return json_output

    @staticmethod
    def _create_override_data_dir_path(terraform_env_path: str, working_dir: str) -> str:
        override_data_dir_path = os.path.join(working_dir, '.cloudrail')
        os.mkdir(override_data_dir_path)
        original_modules_dir = os.path.join(terraform_env_path, '.terraform/modules')
        if os.path.isdir(original_modules_dir):
            new_module_dir = os.path.join(override_data_dir_path, 'modules')
            os.symlink(original_modules_dir, new_module_dir)
        return override_data_dir_path

    @staticmethod
    def _prepare_plugins(root_plugins_dir: str, target_plugins_dir: str):
        logging.info('try unzip plugins to folder {}'.format(target_plugins_dir))
        plugin_dirs = set()
        for plugin_zip_file_name in os.listdir(root_plugins_dir):
            if plugin_zip_file_name.endswith('.zip'):
                plugin_name = os.path.splitext(os.path.basename(plugin_zip_file_name))[0]
                provider = re.search('([^_-]*)_([^_]*)_([^_]*_[^_]*)$', plugin_name)
                provider_name = provider[1]
                provider_version = provider[2]
                provider_arch = provider[3]
                old_plugin_dir = os.path.join(target_plugins_dir, provider_arch)
                new_plugin_dir_prefix = 'registry.terraform.io/hashicorp'
                new_plugin_dir = os.path.join(target_plugins_dir,
                                              new_plugin_dir_prefix,
                                              provider_name,
                                              provider_version,
                                              provider_arch)
                plugin_zip_path = os.path.join(root_plugins_dir, plugin_zip_file_name)
                logging.info('unzip plugin {} into {}'.format(plugin_zip_path, old_plugin_dir))
                with zipfile.ZipFile(plugin_zip_path, 'r') as zip_ref:
                    logging.info('unzip plugin {} into {}'.format(plugin_zip_path, old_plugin_dir))
                    zip_ref.extractall(old_plugin_dir)
                    plugin_dirs.add(old_plugin_dir)
                    if not os.path.exists(new_plugin_dir):
                        logging.info('unzip plugin {} into {}'.format(plugin_zip_path, new_plugin_dir))
                        zip_ref.extractall(new_plugin_dir)
                        plugin_dirs.add(new_plugin_dir)
                os.remove(plugin_zip_path)

        for plugin_dir in plugin_dirs:
            for plugin_file in os.listdir(plugin_dir):
                os.chmod(os.path.join(plugin_dir, plugin_file), 0o777)

    @staticmethod
    def _run_terraform_show(tf_path: str,
                            plan_path: str,
                            terraform_env_path: str,
                            plugins_path: str,
                            override_data_dir_path: str,
                            output_path: str) -> str:
        logging.info(f'running Terraform with {tf_path}, {plan_path}, {terraform_env_path}, {plugins_path}, {override_data_dir_path}, {output_path}')
        terraform = python_terraform.Terraform(working_dir=terraform_env_path, terraform_bin_path=tf_path)
        logging.info('running Terraform show')
        show_output = terraform.show_cmd(plan_path,
                                         no_color=python_terraform.IsFlagged,
                                         json=True,
                                         generate_id_from_address=True,
                                         plugin_cache_dir=plugins_path,
                                         override_data_dir=override_data_dir_path)
        if show_output[0] != 0:
            raise TerraformShowException(TerraformPlanConverter._get_error_from_output(show_output[1]))
        result = show_output[1][2:]
        result_obj = json.loads(result)
        if 'resource_changes' not in result_obj:
            logging.error('terraform show output: {}'.format(show_output[1]))
            logging.error('terraform show logs: {}'.format(show_output[2]))
            raise TerraformShowException(TerraformPlanConverter._get_generic_error())
        with open(output_path, 'w') as file:
            file.write(result)
        return output_path

    @staticmethod
    def _uncompress_tf_env(tf_env_path: str) -> str:
        tf_env_dir = os.path.dirname(tf_env_path)
        working_dir = os.path.join(tf_env_dir, 'working_dir')
        logging.info('uncompressing Terraform env {} to {}'.format(tf_env_path, working_dir))
        with zipfile.ZipFile(tf_env_path, 'r') as zip_ref:
            zip_ref.extractall(working_dir)
        return working_dir

    @staticmethod
    def _uncompress_plan(plan_path: str, working_dir: str) -> str:
        plan_folder = os.path.join(working_dir, 'plan_folder')
        logging.info('uncompressing Terraform plan {} to {}'.format(plan_path, plan_folder))
        try:
            with zipfile.ZipFile(plan_path, 'r') as zip_ref:
                zip_ref.extractall(plan_folder)
        except Exception:
            raise TerraformShowException("""This Terraform plan file has been generated with an unsupported version of Terraform.
Cloudrail supports versions 0.12-0.14""")
        return plan_folder

    @staticmethod
    def _get_state_file(plan_folder: str) -> str:
        state_name = 'tfstate'
        state_path = os.path.join(plan_folder, state_name)
        if os.path.isfile(state_path):
            return state_path
        else:
            raise TerraformShowException('tfstate was not found in working dir')

    @staticmethod
    def _extract_tf_version(state_path: str) -> str:
        with open(state_path) as json_file:
            data = json.load(json_file)
            terraform_version = data['terraform_version']
        logging.info('terraform version {}'.format(terraform_version))
        return terraform_version

    @staticmethod
    def _validate_terraform_version(terraform_version: str):
        min_version = '0.12'
        max_version = '0.15'
        version_range = SimpleSpec('>={},<{}'.format(min_version, max_version))

        if not version_range.match(Version(terraform_version)):
            raise TerraformShowException("""This Terraform plan file has been generated with an unsupported version {} of Terraform.
Cloudrail supports versions 0.12-0.14""".format(terraform_version))

    @staticmethod
    def _prepare_terraform(current_dir: str, tf_version: str) -> str:
        parsed_version = Version(tf_version)
        terraform_file = 'terraform.{}.{}'.format(parsed_version.major, parsed_version.minor)
        tf_path = os.path.join(current_dir, terraform_file)
        return tf_path

    @staticmethod
    def _get_error_from_output(errors: str) -> str:
        logging.error('terraform raw show error: {}'.format(errors))
        parsed_error = TerraformPlanConverter._get_future_syntax_errors(errors) or \
                       TerraformPlanConverter._get_file_not_found(errors) or \
                       TerraformPlanConverter._get_raw_errors(errors) or \
                       TerraformPlanConverter._get_generic_error()
        logging.error('terraform parsed_error: {}'.format(parsed_error))
        return parsed_error

    @staticmethod
    def _get_future_syntax_errors(errors: str) -> Optional[str]:
        known_future_syntax = ['Custom variable validation is experimental',
                               'Reserved argument name in module block',
                               'Provider source not supported']
        future_syntax_regex = '({})'.format('|'.join(known_future_syntax))
        future_syntax_msg = """You are using an unsupported capability ({}). This will be supported at a later date.
In the meantime, please run your TF code with versions 0.12-0.14 and remove any unsupported syntax."""
        future_synatx = set(re.findall(future_syntax_regex, errors))
        if future_synatx:
            return future_syntax_msg.format(','.join(future_synatx))
        else:
            return None

    @staticmethod
    def _get_raw_errors(errors: str):
        error_lines = errors.split('\n')
        error_message = []
        in_error = False
        for line in error_lines:
            if not line:
                continue
            if line.startswith('Warning:') or line.startswith('e:'):
                in_error = False
            if in_error or line.startswith('Error:'):
                in_error = True
                error_message.append(line)
        if error_message:
            return '\n'.join(error_message)
        else:
            return None

    @staticmethod
    def _get_file_not_found(errors: str):
        no_file_regex = r'no file exists at (.*)\.'
        no_file_result = re.findall(no_file_regex, errors)
        if no_file_result:
            file_name = no_file_result[0]
            tf_errors = TerraformPlanConverter._get_raw_errors(errors) or ''
            return f'{tf_errors}' \
                   f'\n\nThe file {file_name} is not found. ' \
                   f'This may be caused by the use of the -v flag when executing this container.' \
                   '\nMake sure that all of the Terraform and related files are included within the path that is mounted.'
        else:
            return None

    @staticmethod
    def _get_generic_error():
        return 'terraform show command returned invalid result'

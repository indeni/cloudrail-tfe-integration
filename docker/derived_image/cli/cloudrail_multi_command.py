import os
import logging
import click


class CloudrailCLI(click.MultiCommand):
    plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')

    def list_commands(self, ctx):
        commands = []
        for filename in os.listdir(self.plugin_folder):
            if not filename.startswith('__init__') and filename.endswith('.py'):
                commands.append(filename[:-3].replace("_", "-"))
        commands.sort()
        return commands

    def get_command(self, ctx, cmd_name):
        globals_locals = {'CLICK_GLOBAL_PATH': self.plugin_folder}
        filenames = [cmd_name, cmd_name.replace("-", "_")]
        # click open bug: https://github.com/pallets/click/issues/1475
        # Fix (not yet part of the stale release) https://github.com/pallets/click/pull/1614/files
        for cmd_file_name in filenames:
            try:
                cmd_full_path = os.path.join(self.plugin_folder, cmd_file_name + '.py')
                if os.path.isfile(cmd_full_path):
                    with open(cmd_full_path) as file:
                        code = compile(file.read(), cmd_full_path, 'exec')
                        # pylint: disable=W0123
                        eval(code, globals_locals, globals_locals)
                    return globals_locals[cmd_file_name]
            except Exception as ex:
                msg = 'error while getting cli command'
                logging.exception(msg)
                raise Exception('{}. Error is:\n{}'.format(msg, str(ex)))
        return None

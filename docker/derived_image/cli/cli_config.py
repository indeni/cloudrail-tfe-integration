import os

from config import Config


class Configuration:
    path = os.path.dirname(os.path.abspath(__file__))
    f = open('{}/conf/config.conf'.format(path))
    config = Config(f)

    @staticmethod
    def get(key: str, default=None):
        return Configuration.config.get(key, default)

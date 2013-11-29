
from os.path import isfile, join
from os import path
from datetime import datetime


BUILD_INFO_PATH = 'build_info'
CURRENT_FILE_PATH = join(BUILD_INFO_PATH, 'current')
EMAIL_FILE_PATH = join(BUILD_INFO_PATH, 'email')
PREVIOUS_FILE_PATH = join(BUILD_INFO_PATH, 'previous')
VERSION_NUMBER = "2.0-dev"


class VersionInfo:

    def __init__(self, startup_time):
        self._startup_time = startup_time

    def fetch(self, all_version_info):
        if all_version_info:
            r_val = []
            self.previous_build_info('.', r_val)
        else:
            r_val = self.build_info('.')
        return r_val

    def build_info(self, dir_name):
        file_name = join(dir_name, CURRENT_FILE_PATH)
        return {'Version': VERSION_NUMBER,
                'Build': self.current_build_info(file_name),
                'Deployed': self.deployed_at(file_name),
                'Person': self._person_id(dir_name)}

    @staticmethod
    def current_build_info(file_name):
        return VersionInfo.file_contents(file_name, 'running-on-dev-box')

    def deployed_at(self, file_name):
        if isfile(file_name):
            mtime = path.getmtime(file_name)
            r_val = datetime.fromtimestamp(mtime)
        else:
            r_val = self._startup_time
        return str(r_val)

    @staticmethod
    def file_contents(file_name, default_rvalue):
        if isfile(file_name):
            with open(file_name, 'r') as f:
                return f.read().strip()
        return default_rvalue

    @staticmethod
    def _person_id(dir_name):
        return VersionInfo.file_contents(join(dir_name, EMAIL_FILE_PATH), 'Brian or Norbert')

    def previous_build_info(self, dir_path, r_val):
        r_val.append(self.build_info(dir_path))
        previous_file_name = join(dir_path, PREVIOUS_FILE_PATH)
        if isfile(previous_file_name):
            self.previous_build_info(join('..', self.file_contents(previous_file_name, '')), r_val)

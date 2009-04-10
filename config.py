import ConfigParser, os, sys
import re
import random
import string
from ConfigParser import NoOptionError

class ConfigException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return str(self.message)

class MelimanConfig:
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        p = os.path.dirname(__file__)
        self.config_files = [
            '/etc/meliman.conf',
            os.path.join(p, 'meliman.conf'),
            ]

        config_exists = False
        for config_file in self.config_files:
            if  os.path.exists(config_file):
                config_exists = True

        if not config_exists:
            raise ConfigException('meliman.conf does not exist.' + \
                  'You must create this file in the application directory before running meliman.') 
        self.config.read(self.config_files)

    def reset(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.config_files)

    def getDatabaseFile(self):
        return self.config.get('Database', 'file')

    def getLibraryInputPath(self):
        return self.config.get('Library', 'input_path')

    def getLibraryMovieInputPath(self):
        try:
            return self.config.get('Library', 'movie_input_path')
        except:
            return None

    def getLibraryTvPath(self):
        return self.config.get('Library', 'tv_path')

    def getLibraryMoviePath(self):
        try:
            return self.config.get('Library', 'movie_path')
        except:
            return None

    def getLibraryFormat(self):
        return self.config.get('Library', 'format')

    def getLibraryRecentPath(self):
        return self.config.get('Library', 'recent_path')

    def getLibraryRecentDurationInMinutes(self):
        return self.config.get('Library', 'recent_duration_in_minutes')

    def getMediaFileExtensions(self):
        return self.config.get('Miscellaneous', 'media_file_extensions')

    def getLockFile(self):
        return self.config.get('Miscellaneous', 'lock_file')

    def getTitleWordsToIgnore(self):
        words_to_ignore_str = self.config.get('Miscellaneous', 'title_words_to_ignore')
        return [w.strip() for w in words_to_ignore_str.split(',')]

    def getTitleCharsToIgnore(self):
        return self.config.get('Miscellaneous', 'title_chars_to_ignore').strip()

    def getWaitFromFileCreationInMinutes(self):
        return self.config.get('Miscellaneous', 'wait_after_file_creation_in_minutes').strip()


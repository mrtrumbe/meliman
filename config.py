import ConfigParser, os, sys
import re
import random
import string
from ConfigParser import NoOptionError

def init():
    global config
    global config_files

    config = ConfigParser.ConfigParser()
    p = os.path.dirname(__file__)
    config_files = [
        '/etc/media_library_manager.conf',
        os.path.join(p, 'media_library_manager.conf'),
        ]

    config_exists = False
    for config_file in config_files:
        if  os.path.exists(config_file):
            config_exists = True

    if not config_exists:
        print 'ERROR:  media_library_manager.conf does not exist.\n' + \
              'You must create this file before running media_library_manager.'
        return 1

    config.read(config_files)
    return 0

def reset():
    global config
    del config
    config = ConfigParser.ConfigParser()
    config.read(config_files)

def getDatabaseFile():
    return config.get('Database', 'file')

def getLibraryInputPath():
    return config.get('Library', 'input_path')

def getLibraryTvPath():
    return config.get('Library', 'tv_path')

def getLibraryFormat():
    return config.get('Library', 'format')

def getLibraryRecentPath():
    return config.get('Library', 'recent_path')

def getLibraryRecentDurationInMinutes():
    return config.get('Library', 'recent_duration_in_minutes')

def getMediaFileExtensions():
    return config.get('Miscellaneous', 'media_file_extensions')

def getLockFile():
    return config.get('Miscellaneous', 'lock_file')

def getTitleWordsToIgnore():
    return config.get('Miscellaneous', 'title_words_to_ignore')

def getTitleCharsToIgnore():
    return config.get('Miscellaneous', 'title_chars_to_ignore')

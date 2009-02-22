import os
import re
import shutil
import unicodedata

from datetime import datetime

import config
import database
import thetvdb
from file_matcher import FileMatcher

RECENT_ADDITIONS = "_Recent Additions"

PY_TIVO_METADATA_EXT = ".txt"

DATE_PATTERN_1='(?P<month1>\d\d)[/-_.](?P<day1>\d\d)[/-_.](?P<year1>\d\d(\d\d)?)'
DATE_PATTERN_2='(?P<year2>\d\d\d\d)[/-_.](?P<month2>\d\d)[/-_.](?P<day2>\d\d)'

FILE_PATTERN_BY_EPISODE='^.*%s.*s(?P<season>\d+)[-_x\.\ ]?e(?P<episode>\d+).*$'
FILE_PATTERN_BY_EPISODE_FOLDERS='^.*%s.*/+season[-_.\ ]*(?P<season>\d+)/+(episode[-_.\ ]*)*(?P<episode>\d+).*$'
FILE_PATTERN_BY_DATE='^.*%s.*\D(' + DATE_PATTERN_1 + '|' + DATE_PATTERN_2 + ')\D.*$'

FILE_NAME='%s-s%02i_e%03i.%s'

class FileManager():
    def __init__(self, config, database, thetvdb, debug):
        self.database = database
        self.thetvdb = thetvdb
        self.debug = debug

        self.lock_file_path = config.getLockFile()
        self.recent_duration_in_minutes = config.getLibraryRecentDurationInMinutes()
        self.recent_path = config.getLibraryRecentPath()

        self.media_file_extension_str = config.getMediaFileExtensions()
        self.file_extensions = self.media_file_extension_str.split(',')

        self.format = config.getLibraryFormat()

        # create FileMatcher objects for each watched series
        self.file_matchers = []
        watched_series = self.database.get_watched_series()
        for series in watched_series:
            self.file_matchers.append(FileMatcher(config, series, debug))


    # returns a tuple of the form: (file_name, series, episode)
    def match_file(self, file_path):
        for file_matcher in self.file_matchers:
            if file_matcher.matches_series_title(file_path):
                if self.debug:
                    print "File '%s' matches series '%s'." % (file_path, file_matcher.series.title)

                matches = file_matcher.match_episode(file_path)
                for match in matches:
                    episode = match.get_episode_metadata(self.database, self.thetvdb)
                    if episode:
                        return (match.file_name, match.series, episode)
        
        # if no matcher matches the file (or if matched episode doesn't exist), return None
        return None


    def generate_metadata(self, episode):
        if self.format == 'pyTivo':
            if self.debug:
                print 'Generating metadata for \'%s\' season %i episode %i in pyTivo format' % (episode.series.title, episode.season_number, episode.episode_number)

            unformatted_metadata = episode.format_for_pyTivo(datetime.now())

            to_return = []
            for l in unformatted_metadata:
                to_append = unicodedata.normalize('NFKD', unicode(l)).encode('ascii', 'ignore')
                to_append = to_append + os.linesep
                to_return.append(to_append)

            return to_return
        else:
            print "Format '%s' is not a valid format.\n" % self.format
            return None




    def copy_media_to_library(self, input_file_path, library_path, library_file_name, move):
        try:
            full_output_path = os.path.join(library_path, library_file_name)

            print "Adding file '%s' to the library.\n" % full_output_path, 

            if not os.path.exists(library_path):
                os.makedirs(library_path)

            if move:
                shutil.move(input_file_path, full_output_path)
            else:
                shutil.copy(input_file_path, full_output_path)
        
            return True
        except:
            return False


    def clear_existing_metadata(self, library_path, library_file_name):
        media_file_path = os.path.join(library_path, library_file_name)
        if self.format == 'pyTivo':
            meta_file_path = media_file_path + PY_TIVO_METADATA_EXT
        else:
            return

        if os.path.exists(meta_file_path):
            os.remove(meta_file_path)


    def write_metadata(self, library_path, library_file_name, episode):
        media_file_path = os.path.join(library_path, library_file_name)
        if self.format == 'pyTivo':
            meta_file_path = media_file_path + PY_TIVO_METADATA_EXT
        else:
            return False

        metadata = self.generate_metadata(episode)
        if metadata is None:
            return False
        else:
            try:
                meta_file = open(meta_file_path, "w")
                try:
                    meta_file.writelines(metadata)
                    meta_file.flush()
                finally:
                    meta_file.close()
            except:
                return False

            return True


    def add_to_recent(self, library_path, library_file_name, episode):
        recent_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_') + library_file_name

        media_file_path = os.path.join(library_path, library_file_name)
        recent_file_path = os.path.join(self.recent_path, recent_file_name)

        if self.format == 'pyTivo':
            meta_file_path = media_file_path + PY_TIVO_METADATA_EXT
            recent_meta_file_path = recent_file_path + PY_TIVO_METADATA_EXT
        else:
            return False

        try:
            if not os.path.exists(self.recent_path):
                os.makedirs(self.recent_path)

            os.symlink(media_file_path, recent_file_path)
            os.symlink(meta_file_path, recent_meta_file_path)

            return True
        except:
            return False


    def cleanup_recent_folder(self):
        files = os.listdir(self.recent_path)
        for f in files:
            if self.is_media_file(f):
                full_path = os.path.join(self.recent_path, f)
                file_timestamp = os.path.getctime(full_path)
                file_time = datetime.fromtimestamp(file_timestamp)

                file_duration = datetime.now() - file_time
                duration_in_minutes = file_duration.seconds/60 + file_duration.days*24*60

                if int(duration_in_minutes) >= int(self.recent_duration_in_minutes):
                    print "Removing file '%s' from recent additions folder.\n" % full_path, 
                    os.remove(full_path)
                    if self.format == 'pyTivo':
                        os.remove(full_path + PY_TIVO_METADATA_EXT)



    def get_process_lock(self):
        if os.path.exists(self.lock_file_path):
            return None
        else:
            lock_file = open(self.lock_file_path, "w")
            lock_file.write("locked")
            lock_file.close()
            return self.lock_file_path

    def relinquish_process_lock(self):
        if os.path.exists(self.lock_file_path):
            os.remove(self.lock_file_path)
            
            



    def is_media_file(self, file_name):
        for e in self.file_extensions:
            pattern = re.compile('^.*\.' + e + '$', re.I)
            if not pattern.match(file_name) is None:
                return True

        return False




    def get_library_file_name(self, file_name, episode):
        extension = file_name.split('.')[-1]
        split_title = [w.strip().lower() for w in episode.series.title.split(' ')]
        return FILE_NAME % ('_'.join(split_title), episode.season_number, episode.episode_number, extension)

    def get_library_path(self, library_base_path, episode):
        title = episode.series.title
        season = episode.season_number
        return os.path.join(library_base_path, title, "Season %02i" % (season,) )



    def get_four_digit_year(self, raw_year):
        if raw_year > 99:
            return raw_year
        elif raw_year > 40:
            return raw_year + 1900
        else:
            return raw_year + 2000
            
        

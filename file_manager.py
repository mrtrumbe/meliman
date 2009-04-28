import os
import re
import shutil

from datetime import datetime

import config
import database
import thetvdb
import utility
from file_matcher import SeriesMatcher
from file_matcher import MovieMatcher

RECENT_ADDITIONS = "_Recent Additions"

PY_TIVO_METADATA_EXT = ".txt"

SERIES_FILE_NAME='%s-s%02i_e%03i.%s'
MOVIE_FILE_NAME='%s (%i) [%i].%s'
MOVIE_WITH_DISC_FILE_NAME='%s (%i) Disc%s [%i].%s'

class FileManager():
    def __init__(self, config, database, thetvdb, moviedb, debug):
        self.database = database
        self.thetvdb = thetvdb
        self.moviedb = moviedb
        self.debug = debug

        self.lock_file_path = config.getLockFile()
        self.recent_duration_in_minutes = config.getLibraryRecentDurationInMinutes()
        self.recent_path = config.getLibraryRecentPath()

        self.tv_genre_path = config.getLibraryTvGenrePath()
        self.movie_genre_path = config.getLibraryMovieGenrePath()

        self.media_file_extension_str = config.getMediaFileExtensions()
        self.file_extensions = self.media_file_extension_str.split(',')

        self.format = config.getLibraryFormat()

        self.wait_from_file_creation_minutes = int(config.getWaitFromFileCreationInMinutes())

        # create SeriesMatcher objects for each watched series
        self.file_matchers = []
        watched_series = self.database.get_watched_series()
        for series in watched_series:
            self.file_matchers.append(SeriesMatcher(config, series, debug))

        #create the pattern for movie files
        self.movie_matcher = MovieMatcher(moviedb, database, config, debug)


    # returns a tuple of the form: (file_name, series, episode)
    def match_file(self, file_path, skip_timecheck):
        if skip_timecheck or self.is_time_to_process_file(file_path):
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


    def match_movie_file(self, file_path, skip_timecheck):
        if skip_timecheck or self.is_time_to_process_file(file_path):
            return self.movie_matcher.match(file_path)

    def is_time_to_process_file(self, file_path):
        now = datetime.now()
        create_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        minutes_from_creation = int((now - create_time).seconds / 60.0)

        if minutes_from_creation > self.wait_from_file_creation_minutes:
            return True
        else:
            print "Will not process file '%s' because it is too soon after file creation time. Minutes since creation: %s  Minutes before processing: %s" % (file_path, minutes_from_creation, self.wait_from_file_creation_minutes)

        return False


    def generate_episode_metadata(self, episode):
        if self.format == 'pyTivo':
            if self.debug:
                print 'Generating metadata for \'%s\' season %i episode %i in pyTivo format' % (episode.series.title, episode.season_number, episode.episode_number)

            unformatted_metadata = episode.format_for_pyTivo(datetime.now())

            to_return = []
            for l in unformatted_metadata:
                to_append = utility.unicode_to_ascii(l)
                to_append = to_append + os.linesep
                to_return.append(to_append)

            return to_return
        else:
            print "Format '%s' is not a valid format.\n" % self.format
            return None


    def generate_movie_metadata(self, movie):
        if self.format == 'pyTivo':
            if self.debug:
                print 'Generating metadata for movie \'%s\' in pyTivo format' % (movie.title, )

            unformatted_metadata = movie.format_for_pyTivo()

            to_return = []
            for l in unformatted_metadata:
                to_append = utility.unicode_to_ascii(l)
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


    def write_metadata(self, library_path, library_file_name, metadata):
        media_file_path = os.path.join(library_path, library_file_name)
        if self.format == 'pyTivo':
            meta_file_path = media_file_path + PY_TIVO_METADATA_EXT
        else:
            return False

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


    def add_to_recent(self, library_path, library_file_name):
        recent_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_') + library_file_name

        media_file_path = os.path.join(library_path, library_file_name)
        recent_file_path = os.path.join(self.recent_path, recent_file_name)

        meta_file_path = None
        if self.format == 'pyTivo':
            meta_file_path = media_file_path + PY_TIVO_METADATA_EXT
            recent_meta_file_path = recent_file_path + PY_TIVO_METADATA_EXT

        try:
            if not os.path.exists(self.recent_path):
                os.makedirs(self.recent_path)

            os.symlink(media_file_path, recent_file_path)

            if meta_file_path is not None:
                os.symlink(meta_file_path, recent_meta_file_path)

            return True
        except:
            return False


    def add_to_genres(self, genre_provider, genre_root_path, library_path, to_add_name, to_add_is_dir):
        if genre_root_path is None:
            return False

        if genre_provider.genres is None or len(genre_provider.genres) == 0:
            return False

        if not os.path.exists(genre_root_path):
            os.makedirs(genre_root_path)

        media_path = os.path.join(library_path, to_add_name)
        meta_path = None
        if not to_add_is_dir and self.format == 'pyTivo':
            meta_path = media_path + PY_TIVO_METADATA_EXT

        for genre in genre_provider.genres:
            if genre is not None and genre.strip() != '':
                genre_path = os.path.join(genre_root_path, genre)
                media_genre_path = os.path.join(genre_path, to_add_name)

                if not os.path.exists(genre_path):
                    os.makedirs(genre_path)

                if not os.path.exists(media_genre_path):
                    os.symlink(media_path, media_genre_path)

                if not to_add_is_dir and self.format == 'pyTivo':
                    meta_genre_path = media_genre_path + PY_TIVO_METADATA_EXT
                    if not os.path.exists(meta_genre_path):
                        os.symlink(meta_path, meta_genre_path)

        return True


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


    def get_series_library_file_name(self, file_name, episode):
        (file, extension) = utility.split_file_name(file_name)
        split_title = [w.strip().lower() for w in episode.series.title.split(' ')]
        return SERIES_FILE_NAME % ('_'.join(split_title), episode.season_number, episode.episode_number, extension)


    def get_movie_library_file_name(self, file_name, movie, disc):
        (file, extension) = utility.split_file_name(file_name)
        if disc is None:
            return MOVIE_FILE_NAME % (movie.title, movie.movie_year, movie.id, extension)
        else:
            return MOVIE_WITH_DISC_FILE_NAME % (movie.title, movie.movie_year, disc, movie.id, extension)


    def get_library_path(self, library_base_path, episode):
        title = episode.series.title
        season = episode.season_number
        return os.path.join(library_base_path, title, "Season %02i" % (season,) )





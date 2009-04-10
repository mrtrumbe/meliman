#!/usr/bin/env python

import sys
import os
import shutil
import sqlite3
import traceback
import re

from optparse import OptionParser, OptionGroup
from datetime import datetime

from config import MelimanConfig
from thetvdb import TheTvDb
from database import Database
from file_manager import FileManager
from moviedb import MovieDB
import metadata
import utility


def main():
    config = MelimanConfig()

    (options, args) = parse_options()

    if options.debug:
        debug = True
    else:
        debug = False

    if options.move:
        move = True
    else:
        move = False

    return do_action(options, args, config, debug, move)



def parse_options():
    usage='''
    usage: %prog action_option [options]

    Exactly one action option (detailed below) must be provided on each run of the script.
    '''
    opt_parser = OptionParser(usage=usage)

    opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Turn on debugging.")
    opt_parser.add_option("-v", "--move", action="store_true", dest="move", help="Move files from the incoming folder to the library instead of copying them.")

    # Lookup Actions
    lookup_group = OptionGroup(opt_parser, "Lookup Actions", "Actions for looking up series, episodes and movies")
    lookup_group.add_option("-s", "--series-lookup", action="store", dest="series_lookup", help="Lookup the TV series matching the provided string.", metavar="SERIES_NAME")
    lookup_group.add_option("-e", "--episode-lookup", action="store", dest="episode_lookup", help="Lookup the TV episode matching the pattern: 'series_id[:season_number[:episode_number]]'", metavar="EPISODE_PATTERN")
    lookup_group.add_option("-o", "--movie-lookup", action="store", dest="movie_lookup", help="Lookup the Movie on IMDb matching the provided text. If only an integer is provided, it is assumed to be the movie's id and the local cache is consulted before going to IMDb. Include the full name of the movie and, in parenthesis, the year the movie was released to better match results on IMDb. Example:\t./meliman.py -o 'Chicago (2002)'", metavar="MOVIE_SEARCH_TEXT")
    opt_parser.add_option_group(lookup_group)
    

    #Watching Actions
    watch_group = OptionGroup(opt_parser, "Series Watching Actions", "Actions for watching, unwatching and listing watched series")
    watch_group.add_option("-w", "--watch-series", action="store", dest="watch_series", help="Tells the application to start watching the series with the provided id.", metavar="SERIES_ID")
    watch_group.add_option("-u", "--unwatch-series", action="store", dest="unwatch_series", help="Tells the application to stop watching the series with the provided id.", metavar="SERIES_ID")
    watch_group.add_option("-a", "--list-watched-series", action="store_true", dest="list_watched_series", help="Lists the series currently being watched by the application.")
    opt_parser.add_option_group(watch_group)


    # Cached Metadata Actions
    cache_group = OptionGroup(opt_parser, "Cached Metadata Actions", "Actions for listing, clearing and refreshing cached metadata")
    cache_group.add_option("-l", "--list-cached-series", action="store_true", dest="list_cached_series", help="Lists all the series cached locally.")
    cache_group.add_option("-L", "--list-cached-movies", action="store_true", dest="list_cached_movies", help="Lists all of the movies cached locally.")
    cache_group.add_option("-c", "--clear-series", action="store", dest="clear_series", help="Clears the local cache of series and episode metadata for the given series.", metavar="SERIES_ID")
    cache_group.add_option("-C", "--clear-movie", action="store", dest="clear_movie", help="Clears the local cache of metadata for the given movie.", metavar="MOVIE_ID")
    cache_group.add_option("-q", "--refresh-series", action="store", dest="refresh_series", help="Clears the local cache of series and episode metadata for the given series and refreshes the metadata from TheTvDb.com.", metavar="SERIES_ID")
    cache_group.add_option("-Q", "--refresh-movie", action="store", dest="refresh_movie", help="Clears the local cache of metadata for the given movie and refreshes the metadata from IMDb.", metavar="MOVIE_ID")
    opt_parser.add_option_group(cache_group)


    # Metadata Generation Actions
    metadata_group = OptionGroup(opt_parser, "Metadata Generation Actions", "Actions for generating metadata and clean file names based on metadata")
    metadata_group.add_option("-f", "--series-name", action="store", dest="series_name", help="Generates a cleaned up version of the file name based on tv series meta data.", metavar="FILE")
    metadata_group.add_option("-F", "--movie-name", action="store", dest="movie_name", help="Generates a cleaned up version of the file name based on movie meta data.", metavar="FILE")
    metadata_group.add_option("-m", "--series-metadata", action="store", dest="series_metadata", help="Outputs metadata for the tv series episode file provided. Does not tag the media.", metavar="EPISODE_FILE")
    metadata_group.add_option("-M", "--movie-metadata", action="store", dest="movie_metadata", help="Outputs metadata for the movie file provided. Does not tag the media.", metavar="MOVIE_FILE")
    opt_parser.add_option_group(metadata_group)


    # Library Management Actions
    library_group = OptionGroup(opt_parser, "Library Management Actions", "Actions for adding to and cleaning up your library")
    library_group.add_option("-r", "--regenerate", action="store_true", dest="regenerate", help="Regenerates metadata for the library directories.  Any existing metadata will be overwritten.")
    library_group.add_option("-g", "--generate_series", action="store", dest="generate_series", help="Recursively traverses the provided directory, generating metadata and tagging each series media file found in the directory.  Any existing metadata will be overwritten.", metavar="DIRECTORY")
    library_group.add_option("-G", "--generate_movies", action="store", dest="generate_movies", help="Recursively traverses the provided directory, generating metadata and tagging each movie media file found in the directory.  Any existing metadata will be overwritten.", metavar="DIRECTORY")
    library_group.add_option("-p", "--process", action="store_true", dest="process", help="Processes files in the incoming directory and organizes the media library.")
    opt_parser.add_option_group(library_group)

    return opt_parser.parse_args()



# **********************************************************
#  Action 'do' methods
# **********************************************************

def do_action(options, args, config, debug, move):
    action_args = (
        options.series_lookup, 
        options.episode_lookup, 
        options.movie_lookup, 

        options.watch_series, 
        options.unwatch_series, 
        options.list_watched_series, 

        options.list_cached_series, 
        options.list_cached_movies, 
        options.clear_series, 
        options.clear_movie, 
        options.refresh_series, 
        options.refresh_movie, 

        options.series_name, 
        options.movie_name, 
        options.series_metadata, 
        options.movie_metadata, 

        options.generate_series, 
        options.generate_movies, 
        options.regenerate, 
        options.process)

    true_count=0
    for arg in action_args:
        if arg:
            true_count=true_count+1

    if true_count == 1:
        if options.series_lookup:
            return do_series_lookup(options.series_lookup, config, debug)
        elif options.episode_lookup:
            return do_episode_lookup(options.episode_lookup, config, debug)
        elif options.movie_lookup:
            return do_movie_lookup(options.movie_lookup, config, debug)

        elif options.watch_series:
            return do_watch_series(options.watch_series, config, debug)
        elif options.unwatch_series:
            return do_unwatch_series(options.unwatch_series, config, debug)
        elif options.list_watched_series:
            return do_list_watched_series(config, debug)

        elif options.list_cached_series:
            return do_list_cached_series(config, debug)
        elif options.list_cached_movies:
            return do_list_cached_movies(config, debug)
        elif options.clear_series:
            return do_clear_series(options.clear_series, config, debug)
        elif options.clear_movie:
            return do_clear_movie(options.clear_movie, config, debug)
        elif options.refresh_series:
            return do_refresh_series(options.refresh_series, config, debug)
        elif options.refresh_movie:
            return do_refresh_movie(options.refresh_movie, config, debug)

        elif options.series_name:
            return do_series_name(options.series_name, config, debug)
        elif options.movie_name:
            return do_movie_name(options.movie_name, config, debug)
        elif options.series_metadata:
            return do_series_metadata(options.series_metadata, config, debug)
        elif options.movie_metadata:
            return do_movie_metadata(options.movie_metadata, config, debug)

        elif options.generate_series:
            return do_generate(options.generate_series, True, config, debug)
        elif options.generate_movies:
            return do_generate(options.generate_movies, False, config, debug)
        elif options.regenerate:
            return do_regenerate(config, debug)
        elif options.process:
            return do_process(config, debug, move)
    else:
        print "ERROR - You must provide exactly one action option."
        return 1


def do_series_lookup(name, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config, debug)

        results = thetvdb.lookup_series_info(name)

        for r in results:
            database.add_series(r)
            print "%i: %s" % (r.id, r.title)

        return 0 
    except:
        traceback.print_exc()
        return 11


def do_episode_lookup(episode_search_pattern, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config, debug)

        split_pattern = episode_search_pattern.split(':')

        if len(split_pattern) < 1 or len(split_pattern) > 3:
            print "Search pattern must be of the form series_id[:season_number[:episode_number]]"
            return 1

        series_id = split_pattern[0]
        series = database.get_series(series_id)
        if series is None:
            print "No series with id '%i' exists in the local cache." % (series_id,)
            return 2

        episodes = get_episodes(thetvdb, database, series)
        if episodes is None:
            print "Could not get episodes for series '%s'." % (series_id,)
            return 3

        if len(split_pattern) == 1:
            print_episodes(episodes)
        elif len(split_pattern) == 2:
            season = int(split_pattern[1])
            print_episodes(database.get_episodes(series_id, season))
        elif len(split_pattern) == 3:
            season = int(split_pattern[1])
            episode = int(split_pattern[2])

            result = get_specific_episode(thetvdb, database, series, season, episode)
            if result is None:
                print "Could not locate an episode matching pattern: %s" % (episode_search_pattern, )
                return 3

            print_episodes([result])

        return 0 
    except:
        traceback.print_exc()
        return 11


def do_movie_lookup(movie_search_text, config, debug):
    try:
        moviedb = MovieDB(config, debug)

        movie_list = moviedb.lookup_movies(movie_search_text)
        if movie_list is None:
            print "No movies match text '%i'." % (movie_search_text,)
            return 2

        for movie in movie_list:
            print_movie(movie)
    except:
        traceback.print_exc()
        return 11


def do_watch_series(series_id_str, config, debug):
    return watch_series_guts(series_id_str, True, config, debug)

def do_unwatch_series(series_id_str, config, debug):
    return watch_series_guts(series_id_str, False, config, debug)

def watch_series_guts(series_id_str, watch, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config, debug)

        try:
            series_id = int(series_id_str)
        except:
            print "Argument is not a valid series id: %s" % (series_id_str, )
            return 2

        series = database.get_series(series_id)
        if series is None:
            series = thetvdb.get_series_info(series_id)
            if series is not None:
                database.add_series(series)

        if not series is None:
            database.watch_series(series, watch)
            return 0
        else:
            print "No series with id '%i' exists in the local cache.  Did you lookup the series?" % (series_id,)
            return 3
    except:
        traceback.print_exc()
        return 11


def do_list_watched_series(config, debug):
    try:
        database = Database(config, debug)

        results = database.get_watched_series()
        print_series(results)
    except:
        traceback.print_exc()
        return 11


def do_list_cached_series(config, debug):
    try:
        database = Database(config, debug)
        results = database.get_all_series()
        print_series(results)
    except:
        traceback.print_exc()
        return 11


def do_list_cached_movies(config, debug):
    try:
        database = Database(config, debug)
        results = database.get_all_movies()
        for r in results:
            print_movie(r)
    except:
        traceback.print_exc()
        return 11


def do_clear_series(series_id_str, config, debug):
    try:
        database = Database(config, debug)

        try:
            series_id = int(series_id_str)
        except:
            print "Argument is not a valid series id: %s" % (series_id_str, )
            return 1

        series = database.get_series(series_id)
        if not series is None:
            database.clear_all_episodes(series.id)
            database.clear_series(series.id)
            print "Series '%s' and all of its episodes have been cleared from the local cache." % (series.title, )
            return 0
        else:
            print "No series with id '%i' exists in the local cache." % (series_id,)
            return 3
    except:
        traceback.print_exc()
        return 11


def do_clear_movie(movie_id_str, config, debug):
    try:
        database = Database(config, debug)

        try:
            movie_id = int(movie_id_str)
        except:
            print "Argument is not a valid movie id: %s" % (movie_id_str, )
            return 1

        movie = database.get_movie(movie_id)
        if not movie is None:
            database.clear_movie(movie.id)
            print "Metadata for movie '%s' has been cleared from the local cache." % (movie.title, )
            return 0
        else:
            print "No movie with id '%i' exists in the local cache." % (movie_id,)
            return 3
    except:
        traceback.print_exc()
        return 11


def do_refresh_series(series_id_str, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config, debug)

        try:
            series_id = int(series_id_str)
        except:
            print "Argument is not a valid series id: %s" % (series_id_str, )
            return 1

        series = database.get_series(series_id)
        if series is not None:
            new_series = thetvdb.get_series_info(series.id)
            new_series.watch = series.watch

            database.clear_series(series.id)
            database.clear_all_episodes(series.id)

            database.add_series(new_series)
            episodes = get_episodes(thetvdb, database, new_series)
        else:
            new_series = thetvdb.get_series_info(series_id)
            series = new_series

            database.add_series(new_series)
            episodes = get_episodes(thetvdb, database, new_series)

        print "Metadata for series '%s' and its episodes has been cleared from the local cache and reloaded from TheTvDb.com." % (series.title, )
        return 0
    except:
        traceback.print_exc()
        return 11


def do_refresh_movie(movie_id_str, config, debug):
    try:
        moviedb = MovieDB(config, debug)
        database = Database(config, debug)

        try:
            movie_id = int(movie_id_str)
        except:
            print "Argument is not a valid movie id: %s" % (movie_id_str, )
            return 1

        database.clear_movie(movie_id)
        new_movie = get_movie_by_id(movie_id, moviedb, database)

        if new_movie is not None:
            print "Metadata for movie '%s' has been cleared from the local cache and reloaded from IMDb.com." % (new_movie.title, )
            return 0
        else:
            print "No movie with id '%i' could be found on IMDb." % (movie_id,)
            return 3
    except:
        traceback.print_exc()
        return 11


def do_series_name(input_file_name, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        moviedb = MovieDB(config, debug)
        database = Database(config, debug)
        file_manager = FileManager(config, database, thetvdb, moviedb, debug)

        match = file_manager.match_file(input_file_name, True)
        if match is None:
            print "File name '%s' doesn't match any series on the watch list." % input_file_name, 
            return 2
        else:
            (file_name, series, episode) = match

        print file_manager.get_series_library_file_name(file_name, episode)
        return 0

    except:
        traceback.print_exc()
        return 11


def do_movie_name(input_file_name, config, debug):
    try:
        moviedb = MovieDB(config, debug)
        thetvdb = TheTvDb(config, debug)
        database = Database(config, debug)
        file_manager = FileManager(config, database, thetvdb, moviedb, debug)

        match = file_manager.match_movie_file(input_file_name, True)
        if match is None:
            print "File name '%s' doesn't match any movies." % input_file_name, 
            return 2
        else:
            (file_name, movie, disc) = match

        print file_manager.get_movie_library_file_name(file_name, movie, disc)
        return 0

    except:
        traceback.print_exc()
        return 11


def do_series_metadata(input_file_path, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        moviedb = MovieDB(config, debug)
        database = Database(config, debug)
        file_manager = FileManager(config, database, thetvdb, moviedb, debug)

        match = file_manager.match_file(input_file_path, True)
        if match is None:
            print "File name '%s' doesn't match any series on the watch list." % input_file_path, 
            return 2
        else:
            (file_name, series, episode) = match

        metadata = file_manager.generate_episode_metadata(episode)
        if metadata is None:
            print "Error generating metadata for file '%s'." % (file_name, )
            return 4

        for l in metadata:
            print l

        return 0
    except:
        traceback.print_exc()
        return 11


def do_movie_metadata(input_file_path, config, debug):
    try:
        moviedb = MovieDB(config, debug)
        database = Database(config, debug)
        thetvdb = TheTvDb(config, debug)
        file_manager = FileManager(config, database, thetvdb, moviedb, debug)

        match = file_manager.match_movie_file(input_file_path, True)
        if match is None:
            print "File name '%s' doesn't match any movie in the local cache or on IMDb." % input_file_path, 
            return 2
        else:
            (file_name, movie, disc) = match

        metadata = file_manager.generate_movie_metadata(movie)
        if metadata is None:
            print "Error generating metadata for file '%s'." % (file_name, )
            return 4

        for l in metadata:
            print l

        return 0
    except:
        traceback.print_exc()
        return 11


def do_generate(input_directory, is_series_dir, config, debug):
    if not os.path.exists(input_directory):
        print "Directory '%s' does not exist. Exiting." % input_directory,
        return 1

    try:
        thetvdb = TheTvDb(config, debug)
        moviedb = MovieDB(config, debug)
        database = Database(config, debug)
        file_manager = FileManager(config, database, thetvdb, moviedb, debug)

        files = []
        for root, dir, files_to_add in os.walk(input_directory):
            for file in files_to_add:
                if file_manager.is_media_file(file):
                    files.append((root, file))

        for (root, file) in files:
            if is_series_dir:
                generate_for_episode_file(file_manager, root, file)
            else:
                generate_for_movie_file(file_manager, root, file)

        return 0
    except:
        traceback.print_exc()
        return 11


def do_regenerate(config, debug):
    tv_path = config.getLibraryTvPath()
    do_generate(tv_path, True, config, debug)

    movie_path = config.getLibraryMoviePath()
    if movie_path is not None:
        do_generate(movie_path, False, config, debug)
    else:
        print "Configuration setting 'movie_path' in section 'Library' is missing. Will not regenerate movie metadata."


def do_process(config, debug, move):
    thetvdb = TheTvDb(config, debug)
    moviedb = MovieDB(config, debug)
    database = Database(config, debug)
    file_manager = FileManager(config, database, thetvdb, moviedb, debug)

    lock = file_manager.get_process_lock()

    if lock is None:
        print "Another instance of media_library_manager is currently processing.  Exiting."
        return 3
    else:
        try:
            input_path = config.getLibraryInputPath()
            tv_path = config.getLibraryTvPath()

            movie_input_path = config.getLibraryMovieInputPath()
            movie_path = config.getLibraryMoviePath()

            process_tv(input_path, tv_path, file_manager, debug, move)

            if movie_input_path is None:
                print "Configuration setting 'movie_input_path' in section 'Library' is missing. Will not attempt processing of movies."
            elif movie_path is None:
                print "Configuration setting 'movie_path' in section 'Library' is missing. Will not attempt processing of movies."
            else:
                process_movies(movie_input_path, movie_path, file_manager, debug, move)

            file_manager.cleanup_recent_folder()
        except:
            traceback.print_exc()
            return 11
        finally:
            file_manager.relinquish_process_lock()





# **********************************************************
#  Helper Methods
# **********************************************************

def get_movie_by_id(id, moviedb, database):
    movie = moviedb.get_movie(id)
    if movie is not None:
        database.add_movie(movie)

    return movie


def process_tv(input_path, tv_path, file_manager, debug, move):
    if not os.path.exists(input_path):
        print "Input path '%s' does not exist. Exiting." % input_path,
        return 1

    if not os.path.exists(tv_path):
        print "Library TV path '%s' does not exist. Exiting." % tv_path,
        return 2

    files = []
    for root, dir, files_to_add in os.walk(input_path):
        for file in files_to_add:
            if file_manager.is_media_file(file):
                files.append((root, file))

    input_contents = os.listdir(input_path)
    for (root, file) in files:
        file_path = os.path.join(root, file)
        if os.path.isfile(file_path):
            process_episode(file_manager, file_path, tv_path, debug, move)



def process_episode(file_manager, input_file_path, tv_path, debug, move):
    try:
        match = file_manager.match_file(input_file_path, False)
        if match is None:
            if debug:
                print "Skipping non-matching or invalid file '%s'.\n" % input_file_path, 

            return
        else:
            (file_name, series, episode) = match

        library_path = file_manager.get_library_path(tv_path, episode)
        library_file_name = file_manager.get_series_library_file_name(file_name, episode)

        if os.path.exists(os.path.join(library_path, library_file_name)):
            print "Skipping file '%s'.  A file for that episode already exists in the library.\n" % input_file_path, 
            return

        if not file_manager.copy_media_to_library(input_file_path, library_path, library_file_name, move):
            print "Error copying media to library.\n"
            return 

        metadata = file_manager.generate_episode_metadata(episode)
        if not file_manager.write_metadata(library_path, library_file_name, metadata):
            print "Error writing metadata to library.\n"
            return 
        
        if not file_manager.add_to_recent(library_path, library_file_name):
            print "Error adding media to recent additions.\n"
            return 
    except:
        traceback.print_exc()
        print "Unexpected error while processing file '%s'. Skipping.\n" % input_file_path, 


def process_movies(input_path, movie_path, file_manager, debug, move):
    if os.path.exists(input_path) and os.path.exists(movie_path):
        files = []
        for root, dir, files_to_add in os.walk(input_path):
            for file in files_to_add:
                if file_manager.is_media_file(file):
                    files.append((root, file))

        input_contents = os.listdir(input_path)
        for (root, file) in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                process_movie(file_manager, file_path, movie_path, debug, move)


def process_movie(file_manager, input_file_path, movie_path, debug, move):
    try:
        match = file_manager.match_movie_file(input_file_path, False)
        if match is None:
            if debug:
                print "Skipping non-matching or invalid file '%s'.\n" % input_file_path, 

            return
        else:
            (file_name, movie, disc) = match

        library_path = movie_path
        library_file_name = file_manager.get_movie_library_file_name(file_name, movie, disc)

        if os.path.exists(os.path.join(library_path, library_file_name)):
            print "Skipping file '%s'.  A file for that episode already exists in the library.\n" % input_file_path, 
            return

        if not file_manager.copy_media_to_library(input_file_path, library_path, library_file_name, move):
            print "Error copying media to library.\n"
            return 

        metadata = file_manager.generate_movie_metadata(movie)
        if not file_manager.write_metadata(library_path, library_file_name, metadata):
            print "Error writing metadata to library.\n"
            return 
        
        if not file_manager.add_to_recent(library_path, library_file_name):
            print "Error adding media to recent additions.\n"
            return 
    except:
        traceback.print_exc()
        print "Unexpected error while processing file '%s'. Skipping.\n" % input_file_path, 



def generate_for_episode_file(file_manager, root, file):
    try:
        file_path = os.path.join(root, file)
        match = file_manager.match_file(file_path, True)
        if match is None:
            print "Skipping non-matching or invalid file '%s'.\n" % file_path, 
            return
        else:
            (file_name, series, episode) = match

        file_manager.clear_existing_metadata(root, file)
        metadata = file_manager.generate_episode_metadata(episode)
        if not file_manager.write_metadata(root, file, metadata):
            print "Error writing metadata.\n"

    except:
        traceback.print_exc()
        print "Unexpected error while processing file '%s'. Skipping.\n" % file_path, 


def generate_for_movie_file(file_manager, root, file):
    try:
        file_path = os.path.join(root, file)
        match = file_manager.match_movie_file(file_path, True)
        if match is None:
            print "Skipping non-matching or invalid file '%s'.\n" % file_path, 
            return
        else:
            (file_name, movie, discnum) = match

        file_manager.clear_existing_metadata(root, file)
        metadata = file_manager.generate_movie_metadata(movie)
        if not file_manager.write_metadata(root, file, metadata):
            print "Error writing metadata.\n"

    except:
        traceback.print_exc()
        print "Unexpected error while processing file '%s'. Skipping.\n" % file_path, 




# Returns all cached episodes (if there are any) or all episodes available from thetvdb
def get_episodes(thetvdb, database, series):
    to_return = database.get_all_episodes(series.id)
    if len(to_return) == 0:
        to_return = thetvdb.get_full_episode_list(series)
        for e in to_return:
            database.add_episode(e, series)

    return to_return


def get_specific_episode(thetvdb, database, series, season_number, episode_number):
    result = database.get_episode(series.id, season_number, episode_number)
    if result is None:
        result = thetvdb.get_specific_episode(series, season_number, episode_number)
        if result is None:
            return None
        else:
            database.add_episode(result, series)

    return result


def print_series(series_list):
    for s in series_list:
        print "%i: %s" % (s.id, utility.unicode_to_ascii(s.title))


def print_episodes(episodes):
    for e in episodes:
        print "%s season %i, episode %i: %s" % (utility.unicode_to_ascii(e.series.title), e.season_number, e.episode_number, utility.unicode_to_ascii(e.title))


def print_movie(movie):
    print "%s: %s (%s)" % (movie.id, utility.unicode_to_ascii(movie.title), movie.movie_year)
    




if __name__ == "__main__":
    exit(main())





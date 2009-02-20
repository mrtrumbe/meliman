#!/usr/bin/env python

import sys
import os
import shutil
import sqlite3
import traceback

from optparse import OptionParser, OptionGroup
from datetime import datetime

from config import MelimanConfig
from thetvdb import TheTvDb
from database import Database
from file_manager import FileManager
import metadata


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
    opt_parser = OptionParser()

    action_group = OptionGroup(opt_parser, "Options Triggering an Action", "Exactly one of these must be present in every run.")
    action_group.add_option("-s", "--series-lookup", action="store", dest="series_lookup", help="Lookup the TV series matching the provided string.", metavar="SERIES_NAME")
    action_group.add_option("-e", "--episode-lookup", action="store", dest="episode_lookup", help="Lookup the TV episode matching the pattern: 'series_id[:season_number[:episode_number]]'", metavar="EPISODE_PATTERN")
    action_group.add_option("-w", "--watch-series", action="store", dest="watch_series", help="Tells the application to start watching the series with the provided id.", metavar="SERIES_ID")
    action_group.add_option("-u", "--unwatch-series", action="store", dest="unwatch_series", help="Tells the application to stop watching the series with the provided id.", metavar="SERIES_ID")
    action_group.add_option("-l", "--list-watched-series", action="store_true", dest="list_watched_series", help="Lists the series currently being watched by the application.")
    action_group.add_option("-c", "--clear-episodes", action="store", dest="clear_episodes", help="Clears the local cache of episodes for a given series.")
    action_group.add_option("-f", "--cleanup-file-name", action="store", dest="cleanup_file_name", help="Generates a cleaned up version of the file name based on meta data.", metavar="FILE")
    action_group.add_option("-m", "--metadata", action="store", dest="metadata", help="Outputs the metadata for the file in question.", metavar="FILE")
    action_group.add_option("-r", "--regenerate", action="store_true", dest="regenerate", help="Regenerates metadata for the library directories.  Any existing metadata will be overwritten.")
    action_group.add_option("-g", "--generate", action="store", dest="generate", help="Recursively traverses the provided directory, generating metadata and tagging each media file found in the directory.  Any existing metadata will be overwritten.", metavar="DIRECTORY")
    action_group.add_option("-p", "--process", action="store_true", dest="process", help="Processes files in the incoming directory and organizes the media library.")
    opt_parser.add_option_group(action_group)

    option_group = OptionGroup(opt_parser, "Additional Options", "None of these are required to run.")
    option_group.add_option("-d", "--debug", action="store_true", dest="debug", help="Turn on debugging.")
    option_group.add_option("-v", "--move", action="store_true", dest="move", help="Move files from the incoming folder to the library instead of copying them.")
    opt_parser.add_option_group(option_group)

    return opt_parser.parse_args()


def do_action(options, args, config, debug, move):
    action_args = (options.series_lookup, options.episode_lookup, options.watch_series, options.unwatch_series, options.list_watched_series, options.clear_episodes, options.cleanup_file_name, options.metadata, options.generate, options.regenerate, options.process)

    true_count=0
    for arg in action_args:
        if arg:
            true_count=true_count+1

    if true_count == 1:
        if options.series_lookup:
            return do_series_lookup(options.series_lookup, config, debug)

        elif options.episode_lookup:
            return do_episode_lookup(options.episode_lookup, config, debug)
        elif options.clear_episodes:
            return do_clear_episodes(options.clear_episodes, config, debug)

        elif options.watch_series:
            return do_watch_series(options.watch_series, config, debug)
        elif options.unwatch_series:
            return do_unwatch_series(options.unwatch_series, config, debug)
        elif options.list_watched_series:
            return do_list_watched_series(config, debug)

        elif options.cleanup_file_name:
            return do_cleanup_file_name(options.cleanup_file_name, config, debug)
        elif options.metadata:
            return do_metadata(options.metadata, config, debug)

        elif options.generate:
            return do_generate(options.generate, config, debug)
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
        database = Database(config)

        results = thetvdb.lookup_series_info(name, debug)

        for r in results:
            database.add_series(r, debug)
            print "%i: %s" % (r.id, r.title)

        return 0 
    except:
        traceback.print_exc()
        return 11


def do_episode_lookup(episode_search_pattern, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config)

        split_pattern = episode_search_pattern.split(':')

        if len(split_pattern) < 1 or len(split_pattern) > 3:
            print "Search pattern must be of the form series_id[:season_number[:episode_number]]"
            return 1

        series_id = split_pattern[0]
        series = database.get_series(series_id)
        if series is None:
            print "No series with id '%i' exists in the local cache.  Did you lookup the series?" % (series_id,)
            return 2

        existing_episode_list = database.get_all_episodes(series_id)
        if len(existing_episode_list) == 0:
            all_episodes = thetvdb.get_full_episode_list(series, debug)
            for e in all_episodes:
                database.add_episode(e, series, debug)


        if len(split_pattern) == 1:
            print_episodes(database.get_all_episodes(series_id))
        elif len(split_pattern) == 2:
            season = int(split_pattern[1])
            print_episodes(database.get_episodes(series_id, season))
        elif len(split_pattern) == 3:
            season = int(split_pattern[1])
            episode = int(split_pattern[2])

            result = get_specific_episode(thetvdb, database, series, season, episode, debug)
            if result is None:
                print "Could not locate an episode matching pattern: %s" % (episode_search_pattern, )
                return 3

            print_episodes([result])

        return 0 
    except:
        traceback.print_exc()
        return 11

def get_specific_episode(thetvdb, database, series, season_number, episode_number, debug):
    result = database.get_episode(series.id, season_number, episode_number)
    if result is None:
        result = thetvdb.get_specific_episode(series, season_number, episode_number, debug)
        if result is None:
            return None
        else:
            database.add_episode(result, series, debug)

    return result




def print_episodes(episodes):
    for e in episodes:
        print "%s season %i, episode %i: %s" % (e.series.title, e.season_number, e.episode_number, e.title)

        
    

def do_watch_series(series_id_str, config, debug):
    return watch_series_guts(series_id_str, True, config, debug)

def do_unwatch_series(series_id_str, config, debug):
    return watch_series_guts(series_id_str, False, config, debug)

def watch_series_guts(series_id_str, watch, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config)

        try:
            series_id = int(series_id_str)
        except:
            print "Argument is not a valid series id: %s" % (series_id_str, )
            return 2

        series = database.get_series(series_id)
        if not series is None:
            database.watch_series(series, watch, debug)
            return 0
        else:
            print "No series with id '%i' exists in the local cache.  Did you lookup the series?" % (series_id,)
            return 3
    except:
        traceback.print_exc()
        return 11


def do_list_watched_series(config, debug):
    try:
        database = Database(config)

        results = database.get_watched_series()
        print_series(results)
    except:
        traceback.print_exc()
        return 11


def print_series(series_list):
    for s in series_list:
        print "%i: %s" % (s.id, s.title)



def do_clear_episodes(series_id_str, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config)

        try:
            series_id = int(series_id_str)
        except:
            print "Argument is not a valid series id: %s" % (series_id_str, )
            return 1

        series = database.get_series(series_id)
        if not series is None:
            database.clear_all_episodes(series.id)
            print "All episodes of series '%s' have been cleared from the local cache." % (series.title, )
            return 0
        else:
            print "No series with id '%i' exists in the local cache.  Did you lookup the series?" % (series_id,)
            return 3
    except:
        traceback.print_exc()
        return 11


def do_cleanup_file_name(input_file_name, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config)
        file_manager = FileManager(config, database, thetvdb)

        file_info = file_manager.get_info_for_file(input_file_name, debug)
        if file_info is None:
            print "File name '%s' doesn't match any series on the watch list." % input_file_name, 
            return 2
        else:
            (file_name, series, episode) = file_info

        print file_manager.get_library_file_name(file_name, episode)
        return 0

    except:
        traceback.print_exc()
        return 11


def do_metadata(input_file_path, config, debug):
    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config)
        file_manager = FileManager(config, database, thetvdb)

        file_info = file_manager.get_info_for_file(input_file_path, debug)
        if file_info is None:
            print "File name '%s' doesn't match any series on the watch list." % input_file_path, 
            return 2
        else:
            (file_name, series, episode) = file_info

        metadata = file_manager.generate_metadata(episode, debug)
        if metadata is None:
            print "Error generating metadata for file '%s'." % (file_name, )
            return 4

        for l in metadata:
            print l

        return 0
    except:
        traceback.print_exc()
        return 11


def do_generate(input_directory, config, debug):
    if not os.path.exists(input_directory):
        print "Directory '%s' does not exist. Exiting." % input_directory,
        return 1

    try:
        thetvdb = TheTvDb(config, debug)
        database = Database(config)
        file_manager = FileManager(config, database, thetvdb)

        files = []
        for root, dir, files_to_add in os.walk(input_directory):
            for file in files_to_add:
                if file_manager.is_media_file(file):
                    files.append((root, file))

        for (root, file) in files:
            generate_for_file(root, file, debug)

        return 0
    except:
        traceback.print_exc()
        return 11

def generate_for_file(file_manager, root, file, debug):
    try:
        file_path = os.path.join(root, file)
        file_info = file_manager.get_info_for_file(file, debug)
        if file_info is None:
            print "Skipping non-matching or invalid file '%s'.\n" % file_path, 
            return
        else:
            (file_name, series, episode) = file_info

        file_manager.clear_existing_metadata(root, file, debug)
        if not file_manager.write_metadata(root, file, episode, debug):
            print "Error writing metadata.\n"

    except:
        traceback.print_exc()
        print "Unexpected error while processing file '%s'. Skipping.\n" % file_path, 

def do_regenerate(config, debug):
    tv_path = config.getLibraryTvPath()
    do_generate(tv_path, config, debug)



def do_process(config, debug, move):
    thetvdb = TheTvDb(config, debug)
    database = Database(config)
    file_manager = FileManager(config, database, thetvdb)

    lock = file_manager.get_process_lock()

    if lock is None:
        print "Another instance of media_library_manager is currently processing.  Exiting."
        return 3
    else:
        try:
            input_path = config.getLibraryInputPath()
            tv_path = config.getLibraryTvPath()

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
                    process_file(file_manager, file_path, tv_path, debug, move)

            file_manager.cleanup_recent_folder()
        except:
            traceback.print_exc()
            return 11
        finally:
            file_manager.relinquish_process_lock()


def process_file(file_manager, input_file_path, tv_path, debug, move):
    try:
        file_info = file_manager.get_info_for_file(input_file_path, debug)
        if file_info is None:
            print "Skipping non-matching or invalid file '%s'.\n" % input_file_path, 
            return
        else:
            (file_name, series, episode) = file_info

        library_path = file_manager.get_library_path(tv_path, episode)
        library_file_name = file_manager.get_library_file_name(file_name, episode)

        if os.path.exists(os.path.join(library_path, library_file_name)):
            print "Skipping file '%s'.  A file for that episode already exists in the library.\n" % input_file_path, 
            return
        else:
            if not file_manager.copy_media_to_library(input_file_path, library_path, library_file_name, move):
                print "Error copying media to library.\n"
                return 
            
            if not file_manager.write_metadata(library_path, library_file_name, episode, debug):
                print "Error writing metadata to library.\n"
                return 
            
            if not file_manager.add_to_recent(library_path, library_file_name, episode):
                print "Error adding media to recent additions.\n"
                return 
    except:
        traceback.print_exc()
        print "Unexpected error while processing file '%s'. Skipping.\n" % input_file_path, 


if __name__ == "__main__":
    exit(main())






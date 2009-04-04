#!/usr/bin/env python

import sys
import os
import shutil
import sqlite3
import re

from optparse import OptionParser, OptionGroup

from datetime import datetime

SCHEMA_PATTERN = '(?P<migration>\d+)\.sql'
VERSION_INSERT_SQL = 'insert into version (version, description, migration_timestamp) values (?, ?, ?)'


def main():
    (options, args) = parse_options()
    return do_action(options, args)


def parse_options():
    usage = '''
    usage: %prog action_option [options] [database_file]

    database_file is the path to a sql3lite file or the path to a new file to create.
    '''

    opt_parser = OptionParser(usage=usage)

    action_group = OptionGroup(opt_parser, "Action Options", "Exactly one of these options must be given for each execution of the script.")
    action_group.add_option("-t", "--to_migration", action="store", dest="to_migration", help="Migrate the provided database to the specified migration number. This action will execute all migrations inclusive to the range [database version + 1:provided migration number] from the local schema directory. Value may be a number representing a specific migration or HEAD which represents the highest migration available in the local schema directory. Requires user to provide the database_file argument.", metavar="MIGRATION")
    action_group.add_option("-d", "--database_info", action="store_true", dest="database_info", help="Print information about the database file. Requires user to provide the database_file argument.")
    action_group.add_option("-i", "--schema_info", action="store_true", dest="schema_info", help="Print information about the local schema directory.")
    action_group.add_option("-f", "--force_version", action="store", dest="force_version", help="Forced the version number of the database to the provided number.  This action does not apply any migrations from the local schema directory. Requires user to provide the database_file argument.", metavar="VERSION_TO_FORCE")
    opt_parser.add_option_group(action_group)

    opt_parser.add_option("-s", "--schema_directory", action="store", dest="schema_directory", help="The schema directory to use when looking for migrations. If a relative path is provided, it is assumed to be relative to the location of the script being run.", default="../db", metavar="SCHEMA_DIRECTORY")
    opt_parser.add_option("-p", "--print_only", action="store_true", dest="print_only", help="The script won't execute any sql, but rather just print out the sql it would execute.", default=False)

    return opt_parser.parse_args()



def do_action(options, args):
    action_args = (options.to_migration, options.database_info, options.schema_info, options.force_version)

    true_count=0
    for arg in action_args:
        if arg:
            true_count=true_count+1

    if true_count == 1:
        if options.to_migration:
            return do_to_migration(options.to_migration, options.schema_directory, get_database(args), options.print_only)

        elif options.database_info:
            return do_database_info(get_database(args))

        elif options.schema_info:
            return do_schema_info(options.schema_directory)

        elif options.force_version:
            return do_force_version(options.force_version, get_database(args))
    else:
        raise Exception("ERROR - You must provide exactly one action option.")


def get_database(args):
    if len(args) > 0:
        return sqlite3.connect(args[0])
    else:
        raise Exception("ERROR - This action requires the database_file argument.")


def do_to_migration(migration_number, schema_directory, database, print_only):
    version = get_database_version(database)
    migrations = get_migrations(schema_directory)

    if migration_number == 'HEAD':
        requested_number = migrations[-1][2]
    else:
        try:
            requested_number = int(migration_number)
        except:
            raise Exception("Provided migration number (%s) is invalid." % (migration_number, ))
    
    if requested_number == version:
        print "Database already at version %s. Exiting. \n" % (version, )
        return
    elif requested_number < version:
        print "Requested migration (%s) is less than current database version (%s)." % (requested_number, version)
        return

    print "Existing database has version %s. Will migrate to version %s." % (version, requested_number)
        
    for (path, file, number) in migrations:
        if number > version and number <= requested_number:
            migration_text = ''
            try:
                migration_text = read_migration_text(path, file)
            except Exception as ex:
                raise Exception("Unexpected error reading text of migration %s: %s" % (number, str(ex)))
            
            if print_only:
                print "-- Migration %s text:\n\n%s" % (number, migration_text)
            else:
                print "-- Applying migration %s to the database." % (number, )

                try:
                    database.executescript(migration_text)
                    database.commit()
                except Exception as ex:
                    database.rollback()
                    if migration_text != '':
                        print migration_text
                    raise Exception("Unexpected exception applying migration %s: %s" % (number, str(ex)))

                insert_database_version(number, 'automatically migrated successfully.', database)
    print "Migrated to version %s successfully." % requested_number


def do_database_info(database):
    print "Current database version: %i\n" % get_database_version(database)


def do_schema_info(schema_directory):
    migrations = get_migrations(schema_directory)
    print "Found %s migrations in schema directory '%s'." % (len(migrations), schema_directory)
    if len(migrations) > 0:
        print "Current highest migration: %s (%s)" % (migrations[-1][2], migrations[-1][1])


def do_force_version(version_number, database):
    print "Forcing database to version %s.\n" % (version_number, )
    insert_database_version(version_number, 'Forcing database to version %s.' % (version_number, ), database)
    print "Database has been successfully forced to version %s.\n" % (version_number, )
    



def get_migrations(schema_directory):
    c = os.getcwd()
    p = os.path.dirname(__file__)
    os.chdir(p)
    files = os.listdir(schema_directory)
    os.chdir(c)

    migrations = []
    schema_file_re = re.compile(SCHEMA_PATTERN)
    for f in files:
        match = schema_file_re.match(f)
        if match:
            migrations.append((schema_directory, f, int(match.group('migration'))))

    if len(migrations) == 0:
        raise Exception("No migrations exist in schema directory '%s'." % (schema_directory, ))

    # sort migrations by their number
    migrations.sort(lambda x, y: x[2]-y[2])

    return migrations

def read_migration_text(path, file):
    c = os.getcwd()
    p = os.path.dirname(__file__)
    os.chdir(p)

    f = open(os.path.join(path, file), 'r')
    to_return = ''
    try:
        for l in f:
            to_return += l
    finally:
        f.close()
        os.chdir(c)

    return to_return

def get_database_version(database):
    try:
        sql = 'select version from version order by id desc limit 1;'
        c = database.cursor()
        c.execute(sql)

        results = c.fetchall()
        if len(results) == 1:
            r = results[0]
            return r[0]
        else:
            return 0
    except Exception as ex:
        # this _likely_ means there is no version table
        return 0

def insert_database_version(version, comment, database):
    try:
        database.execute(VERSION_INSERT_SQL, (version, comment, str(datetime.now())))
        database.commit()
    except Exception as ex:
        database.rollback()
        raise Exception("Unexpected exception writing version to the database: %s" % (str(ex), ))



if __name__ == "__main__":
    exit(main())


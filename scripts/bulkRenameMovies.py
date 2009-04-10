#! /usr/bin/env python

import os
import shutil
import sys

MV_FORMAT_STRING = "mv \"%s\" \"%s\""
MV_FAILURE_FORMAT_STRING = "Failed to complete this operation: mv \"%s\" \"%s\""

def main(args):
    (instruction_file, movie_directory) = process_args(args)
    if instruction_file is None:
        return 1

    instructions = read_instructions(instruction_file)

    c = os.getcwd()
    os.chdir(movie_directory)

    all_renames_succeeded = True

    for i in instructions:
        (src, dst) = i
        try:
            shutil.move(src, dst)
            print MV_FORMAT_STRING % i
        except:
            print MV_FAILURE_FORMAT_STRING % i
            all_renames_succeeded = False

    os.chdir(c)

    if all_renames_succeeded:
        print "Renaming completed successfully."
        return 0
    else:
        print "Not all renames completed successfully."
        return 2


def process_args(args):
    if len(args) != 3:
        usage = '''
        usage: bulkRenameMovies.py movie_rename_instruction_file movie_directory
        '''
        print usage
        return (None, None)
    
    instruction_file = args[1]
    movie_directory = args[2]

    if not os.path.isfile(instruction_file):
        print "provided movie_rename_instruction_file does not exist or isn't a file"
        return (None, None)

    if not os.path.isdir(movie_directory):
        print "provided movie_directory does not exist or isn't a directory"
        return (None, None)

    return (instruction_file, movie_directory)


def read_instructions(instruction_file):
    to_return = []
    f = open(instruction_file, 'r')
    try:
        for l in f:
            split_line = l.split(';')
            if len(split_line) != 2:
                raise Exception("Improperly formatted movie_rename_instruction_file.  Each line should be of the format: oldname; newname")

            to_return.append((split_line[0].strip(), split_line[1].strip()))
    finally:
        f.close()

    return to_return


if __name__ == "__main__":
    exit(main(sys.argv))


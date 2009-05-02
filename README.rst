===========
 Meliman
===========

-------------------------------------------------------
 A tool for organizing and tagging your media library.
-------------------------------------------------------

    Currently unversioned.
    Meliman is distributed under the BSD license. See LICENSE.txt for more information.


USAGE
=====

Managing TV series with Meliman is based on a "watched series" strategy: rather than 
guessing which series a file belongs to, a user first sets up a list of series which 
the program will then watch for.  Typically, operation of Meliman for TV series will 
look something like this::

    # ./meliman.py -s "The Simpsons"
    71663: The Simpsons
    79421: The Simpsons Shorts

    # ./meliman.py -w 71663
    Will now watch series 'The Simpsons'.

    # ./meliman.py -m simpsons_s4e7.avi
    isEpisode : true
    title : Marge Gets A Job
    time : 2008-12-17T10:19:47Z
    description: #7.  The Simpsons' house begins sinking ...
    
    # ./meliman.py -a
    71663: The Simpsons

Here, we first look up series matching the string "The Simpsons", then we tell 
Meliman to watch the series based on its id, then we feed a file to Meliman and 
have it generate metadata, and finally we list the series we are currently watching.  
Note that the -m option just prints the metadata, it doesn't tag the file.

Meliman also supports movies.  Here, because of practicality, we abandon the watch
strategy and do a lookup against IMDb.  Most operations against series are also 
available for movies by just capitalizing the option. Here is what operations for 
movies look like::

    # ./meliman.py -o "The Simpsons"
    96697: The Simpsons (1989)
    462538: The Simpsons Movie (2007)
    296852: The Simpsons (1991)
    1139628: The Simpsons Game (2007)
    ...

    # ./meliman.py -M "The Simpsons Movie (2007).avi"
    isEpisode : false
    title : The Simpsons Movie
    movieYear : 2007
    ...

    # ./meliman.py -F "The Simpsons Movie (2007).avi"
    The Simpsons Movie (2007) [462538].avi

Here, we first search for a movie using some text.  Notice that we get a lot of 
search hits here.  Because we aren't using a watching strategy, we need to be 
very specific with our search text and media file naming.  The best strategy (and
the one we use in the example) is to use the full name of the movie followed by
the year the movie was released in parenthesis.  That way, you can be sure that
meliman matches the exact movie you want.  The second command in this example
generates metadata for the media file and the third generates a library friendly
version of the media file's name.

Once you have started watching some TV series with Meliman, you can use Meliman to
watch an incoming directory and copy/move media files to your library directory, 
tagging the file with metadata in the process.  To make this work, you'll need to 
properly setup entries in your configuration file.  These settings, in particular, 
are important::

    input_path=/src/meliman/tmp/input
    movie_input_path=/src/meliman/tmp/movie_input
    tv_path=/src/meliman/tmp/tv
    movie_path=/src/meliman/tmp/movies
    recent_path=/src/meliman/tmp/recent

Once you are properly configured, you should be able to run meliman in "process mode," 
like this::

    # ./meliman.py -p
    Skipping file '/src/meliman/tmp/input/the_simpsons_s5e8.avi'.  
        A file for that episode already exists in the library.
    Adding file '/src/meliman/tmp/tv/The Simpsons/Season 05/the_simpsons-s05_e009.avi' 
        to the library.
    Removing file '/src/meliman/tmp/recent/2009-02-22_09-48-14_the_simpsons-s05_e008.avi' 
        from recent additions folder.

You can move/edit files in your library, but it may cause meliman to not understand
files it previously moved to the library.  As you can see from the output above,
Meliman tries to keep a neat library, not moving duplicate files to the library,
cleaning up the recent additions folder, etc.  Meliman simply skips files which 
don't match a watched series title or those files which don't match a real episode
of a given series.

More information about running Meliman can be found in the template configuration
file and using meliman's help option::

    # ./meliman.py --help

FEATURES
========

Feature list:
    * Lookup series from thetvdb.com based on a search string
    * Lookup episodes from thetvdb.com based on a search string
    * Lookup movies from imdb.com based on a search string
    * Caches movies, series and episode data locally to prevent frequent network access
    * Generates cleaned-up file names for media files based on metadata
    * Generates metadata for media files
    * Manages a library directory structured by series name, seasons and episode numbers
    * Generates Genre folders for series and movies 
    * Watches an incoming directory for new media files and copies those files to 
      the library, properly tagging and naming those files
    * Maintains a list of recently added media files in the library

Planned improvements:
    * Arbitrary media file tagging (not using -p or the generate options)
    * Support more metadata formats (like mp4 file tagging for AppleTV)
    * Ability to run meliman as a server
    * A web-based GUI


INSTALLATION
============ 

Requirements: 
    * Python 2.5 or greater (http://www.python.org)
        Python 3000 will almost surely *not* work.
    * imdbpy (http://imdbpy.sourceforge.net/)
        The easiest way to get imdbpy is probably through setup tools/easy_install.  
        Get setup tools here: http://peak.telecommunity.com/DevCenter/EasyInstall#installation-instructions
        Once you've installed easy_install, install imdbpy using::
            easy_install imdbpy
        You may need to run this with sudo or otherwise escalate your priviledges.
    * A unix-like OS
        While some effort was made to make meliman cross-platform, it has never
        been tested on Windows.  It should run fine on Linux and Mac OS X and
        has been tested on these systems.  Any help in ensuring meliman is truly
        cross platform would be appreciated.

Installation of Meliman is pretty simple:
    1. Put the Meliman folder wherever you like on your computer (referred to from
       here on as INSTALL_PATH).
    2. Create a db file for local caching::
         cd INSTALL_PATH
         python ./scripts/syncdb.py -t HEAD /path/to/new/or/existing/db/file
    3. Create a config file for the application::
         cp INSTALL_PATH/Meliman.conf.dist INSTALL_PATH/Meliman.conf
    4. Edit the config file to point to your db file and the various directories you want 
       to use on your computer.  The example config file is well documented to help you 
       make sensible settings.

Once you have installed the application, you can immediately use the meliman.py 
script to operate the program.  Execute the follwing for more information::

    INSTALL_PATH/meliman.py --help



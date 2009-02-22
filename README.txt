Meliman - A tool for organizing and tagging your media library.

Currently unversioned.


== FEATURES ==

Meliman currently supports only tv series.  Support for movies is planned.

Meliman is based on a "watched series" strategy: rather than guessing which 
series a file belongs to, a user first sets up a list of series which the program will then 
watch for.  Typically, operation of Meliman will look something like this:

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

Here, we first look up series matching the string "The Simpsons", then we tell 
Meliman to watch the series based on its id, then we feed a file to 
Meliman and have it generate metadata.  The -m option just prints the metadata.

Once you have started watching some series with Meliman, you can use Meliman to
watch an incoming directory and copy/move media files to a library directory, tagging
the file with metadata in the process.  To make this work, you'll want to properly 
setup entries in your configuration file.  These three settings, in particular, are 
important:

    input_path=/src/meliman/tmp/input
    tv_path=/src/meliman/tmp/tv
    recent_path=/src/meliman/tmp/recent

Once you are properly configured, you should be able to run meliman in "process mode," 
like this:

    # ./meliman.py -p
    Skipping file '/src/meliman/tmp/input/the_simpsons_s5e8.avi'.  
        A file for that episode already exists in the library.
    Adding file 
        '/src/meliman/tmp/tv/The Simpsons/Season 05/the_simpsons-s05_e009.avi' 
        to the library.
    Removing file 
        '/src/meliman/tmp/recent/2009-02-22_09-48-14_the_simpsons-s05_e008.avi' 
        from recent additions folder.

You can move/edit files in your library, but it may cause meliman to not understand
files it previously moved to the library.  As you can see from the output above,
Meliman tries to keep a neat library, not moving duplicate files to the library,
cleaning up the recent additions folder, etc.  Meliman simply skips files which 
don't match a watched series title or those files which don't match a real episode
of a given series.

More information about running Meliman can be found in the template configuration
file and using meliman's help option:

    # ./meliman.py --help


Feature list:
    - Lookup series from thetvdb.com based on a search string
    - Lookup episodes from thetvdb.com based on a search string
    - Caches series and episode data locally to prevent frequent network access
    - Generates cleaned-up file names for media files based on metadata
    - Generates metadata for media files
    - Manages a library directory structured by series name, seasons and episode numbers
    - Watches an incoming directory for new media files and copies those files to the library
    - Maintains a list of recently added media files in the library

Planned improvements:
    - Arbitrary media file tagging (not using -p or the generate options)
    - Faster performance (better thetvdb usage, better pattern matching, etc.)
    - Support more metadata formats (like mp4 file tagging for AppleTV)
    - Ability to run meliman as a server
    - A web-based GUI


== INSTALLATION ==

Requirements: 
    - Python 2.5 (http://www.python.org)

Installation of Meliman is pretty simple:
    - Put the Meliman folder wherever you like on your computer (referred to from
        here on as INSTALL_PATH).
    - Create a db file for local caching:
        cp INSTALL_PATH/metadata.db.dist DESIRED_DB_FILE_LOCATION
    - Create a config file for the application:
        cp INSTALL_PATH/Meliman.conf.dist INSTALL_PATH/Meliman.conf
    - Edit the config file to point to your db file and the various directories you want to 
        use on your computer.  The example config file is well documented to help you make
        sensible settings.

Once you have installed the application, you can immediately use the meliman.py 
script to operate the program.  Execute the follwing for more information:

    INSTALL_PATH/meliman.py --help


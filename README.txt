Meliman - A tool for organizing and tagging your media library.

Current version: v0.5


== FEATURES ==

Meliman currently supports only tv series.  Support for movies is planned.

Meliman is based on a "watched series" strategy: rather than guessing which 
series a file belongs to, a user first sets up a list of series which the program will then 
watch for.  Typically, operation of Meliman will look something like this:

    # ./Meliman.py -s "The Simpsons"
    71663: The Simpsons
    79421: The Simpsons Shorts

    # ./Meliman.py -w 71663
    Will now watch series 'The Simpsons'.

    # ./Meliman.py -m simpsons_s4e7.avi
    isEpisode : true
    title : Marge Gets A Job
    time : 2008-12-17T10:19:47Z
    description: #7.  The Simpsons' house begins sinking ...

Here, we first look up series matching the string "The Simpsons", then we tell 
Meliman to watch the series based on its id, then we feed a file to 
Meliman and have it generate metadata.

Feature list:
    - Lookup series from thetvdb.com based on a search string.
    - Lookup episodes from thetvdb.com based on a search string.
    - Caches series and episode data locally to prevent frequent network access.
    - Generates cleaned-up file names for media files based on metadata.
    - Generates metadata for media files.
    - Manages a library directory structured by series name, seasons and episode numbers.
    - Watches an incoming directory for new media files and copies those files to the library.
    - Maintains a list of recently added media files in the library.


== INSTALLATION ==

Requirements: 
    - Python 2.5 (http://www.python.org)
    - CherryPy 3.1 or greater (Only required if you intend to run daemon mode...get 
            cherrypy here: http://www.cherrypy.org)

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

Once you have installed the application, you can immediately use the Meliman.py 
script to operate the program.  Execute the follwing for more information:

    INSTALL_PATH/Meliman.py --help

Running the Meliman.py script is referred to as "manual mode".  There is also a
daemon mode supported which will run various commands on a schedule and also provide a web
interface for remote execution of the program.  Documentation of daemon mode is forthcoming.


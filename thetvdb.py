import urllib2
import zipfile
import StringIO
import random

from datetime import datetime
from xml.etree.ElementTree import parse, Element, SubElement

import metadata

MIRROR_URL = 'http://www.thetvdb.com/api/%s/mirrors.xml'
SERVER_TIME_URL = '/api/%s/updates/' 
SERIES_LOOKUP_URL = '/api/GetSeries.php?seriesname=%s'
SERIES_URL = '/api/%s/series/%s/en.xml'
EPISODE_URL = '/api/%s/series/%i/default/%i/%i/en.xml'
EPISODE_HISTORY_URL = '/api/%s/series/%i/all/en.zip'
EPISODE_LOOKUP_BY_DATE_URL = '/api/GetEpisodeByAirDate.php?apikey=%s&seriesid=%i&airdate=%s&language=en'

API_KEY = "0403764A0DA51955"


# this finds an acceptable mirror for future thetvdb requests.
def init(config, debug):
    global active_mirror

    full_url = MIRROR_URL % (API_KEY, )

    mirrors_xml = parse(urllib2.urlopen(full_url))
    mirrors = mirrors_xml.findall('Mirror')

    random.seed()
    mirror_to_get = random.randrange(0, len(mirrors), 1)

    mirror = mirrors[mirror_to_get]
    active_mirror = mirror.findtext('mirrorpath')

    if debug:
        print "Using thetvdb mirror: %s" % (active_mirror, )



# returns an integer timestamp
def get_server_time(debug):
    global active_mirror
    full_url = active_mirror + SERVER_TIME_URL % (API_KEY, )

    if debug:
        print "Getting data for url: %s" % full_url

    series_xml = parse(urllib2.urlopen(full_url))
    data_element = series_xml.getroot()
    to_return = int(data_element.attrib['time'])

    if debug:
        print "    result: %i" % to_return

    return to_return


# returns a metadata.Series object
def lookup_series_info(name, debug):
    global active_mirror
    full_url = active_mirror + SERIES_LOOKUP_URL % (name.strip().replace(' ', '%20'),)

    if debug:
        print "Getting data for url: %s" % full_url

    series_xml = parse(urllib2.urlopen(full_url))
    series = [Series for Series in series_xml.findall('Series')]

    # now that we have the id's, get the full series info
    full_series = []
    for s in series:
        id = get_int(s, 'id', 0)
        full_url = active_mirror + SERIES_URL % (API_KEY, id)
        full_series_xml = parse(urllib2.urlopen(full_url))
        for full_s in full_series_xml.findall('Series'):
            full_series.append(full_s)
        
    if debug:
        print "    found %i series:" % len(full_series)

    to_return = []
    
    for s in full_series:
        s_obj = parse_series_xml(s)
        to_return.append(s_obj)

        if debug:
            print "    found series '%s'" % s_obj.title

    return to_return


# returns a list of metadata.Episode objects: 
def get_full_episode_list(series, debug):
    global active_mirror
    full_url = active_mirror + EPISODE_HISTORY_URL % (API_KEY, series.id)

    if debug:
        print "Getting data for url: %s" % full_url

    zip_stream = urllib2.urlopen(full_url)
    zip_file_string = create_string_from_stream(zip_stream, debug)
    local_stream = StringIO.StringIO(zip_file_string)
    zip_file = zipfile.ZipFile(local_stream)

    episode_xml = zip_file.read('en.xml')
    to_return = parse_episode_xml(episode_xml, series, debug)

    return to_return


# returns a metadata.Episode object
def get_specific_episode(series, season_number, episode_number, debug):
    global active_mirror
    full_url = active_mirror + EPISODE_URL % (API_KEY, series.id, season_number, episode_number)

    if debug:
        print "Getting data for url: %s" % full_url

    try:
        xml_stream = urllib2.urlopen(full_url)
        xml_file_string = create_string_from_stream(xml_stream, debug)
        to_return = parse_episode_xml(xml_file_string, series, debug)

        return to_return[0]
    except urllib2.HTTPError:
        return None


# returns a metadata.Episode object
def get_specific_episode_by_date(series, year, month, day, debug):
    global active_mirror

    formatted_date='%i-%i-%i' % (year, month, day)
    full_url = active_mirror + EPISODE_LOOKUP_BY_DATE_URL % (API_KEY, series.id, formatted_date)

    if debug:
        print "Getting data for url: %s" % full_url

    try:
        xml_stream = urllib2.urlopen(full_url)
        xml_file_string = create_string_from_stream(xml_stream, debug)
        to_return = parse_episode_xml(xml_file_string, series, debug)

        return to_return[0]
    except urllib2.HTTPError:
        return None




def create_string_from_stream(stream, debug):
    to_return = ''

    try:
        while True:
            to_return = to_return + stream.next()
    except:
        to_return = to_return

    return to_return



def parse_series_xml(series_xml):
    to_return = metadata.Series()

    to_return.id = get_int(series_xml, 'id', -1)
    to_return.zap2it_id = get_string(series_xml, 'zap2it_id', '')
    to_return.imdb_id = get_string(series_xml, 'IMDB_ID', '')
    to_return.title = get_string(series_xml, 'SeriesName', '')
    to_return.description = get_string(series_xml, 'Overview', '')
    to_return.actors = get_string_list(series_xml, 'Actors', '|', [])
    to_return.genres = get_string_list(series_xml, 'Genre', '|', [])
    to_return.content_rating = get_string(series_xml, 'ContentRating', '')

    return to_return



def parse_episode_xml(xml_string, series, debug):
    xml_stream = StringIO.StringIO(xml_string)
    xml_object = parse(xml_stream)
    episodes = [Episode for Episode in xml_object.findall('Episode')]

    to_return = []

    for episode in episodes:
        episode_metadata = metadata.Episode()
        to_return.append(episode_metadata)

        episode_metadata.series = series;

        episode_metadata.title = get_string(episode, 'EpisodeName', '')
        episode_metadata.description = get_string(episode, 'Overview', '')
        episode_metadata.rating = get_float(episode, 'Rating', 0.0)

        episode_metadata.season_number = get_int(episode, 'SeasonNumber', 0)
        episode_metadata.episode_number = get_int(episode, 'EpisodeNumber', 0)

        episode_metadata.director = get_string(episode, 'Director', '')
        episode_metadata.host = get_string(episode, 'Host', '') 
        episode_metadata.writers = get_string_list(episode, 'Writer', ',', [])
        episode_metadata.guest_stars = get_string_list(episode, 'GuestStars', '|', [])

        episode_metadata.original_air_date = get_datetime(episode, 'FirstAired', 
                None, debug)
        episode_metadata.time = datetime.now()


    return to_return


def get_string(xml_element, sub_element_name, default):
    try:
        return xml_element.findtext(sub_element_name)
    except:
        return default

def get_string_list(xml_element, sub_element_name, separator, default):
    try:
        text = xml_element.findtext(sub_element_name)
        return text.split(separator)
    except:
        return default

def get_int(xml_element, sub_element_name, default):
    try:
        return int(xml_element.findtext(sub_element_name))
    except:
        return default

def get_float(xml_element, sub_element_name, default):
    try:
        return float(xml_element.findtext(sub_element_name))
    except:
        return default

def get_datetime(xml_element, sub_element_name, default, debug):
    try:
        date_text = xml_element.findtext(sub_element_name)
        return datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        if debug:
            print "Error parsing string '%s' into datetime.\n" % date_text, 
        return default
    except:
        return default



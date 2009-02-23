import os
import re

DATE_PATTERN_1='(?P<month1>\d\d)[/-_.](?P<day1>\d\d)[/-_.](?P<year1>\d\d(\d\d)?)'
DATE_PATTERN_2='(?P<year2>\d\d\d\d)[/-_.](?P<month2>\d\d)[/-_.](?P<day2>\d\d)'

FILE_PATTERN_BY_EPISODE='^.*s(?P<season>\d+)[-_x\.\ ]?e(?P<episode>\d+).*$'
FILE_PATTERN_BY_EPISODE_FOLDERS='^.*/+season[-_.\ ]*(?P<season>\d+)/+(episode[-_.\ ]*)*(?P<episode>\d+).*$'
FILE_PATTERN_BY_DATE='^.*\D(' + DATE_PATTERN_1 + '|' + DATE_PATTERN_2 + ')\D.*$'

SERIES_TITLE_SEPARATOR_PATTERN='[^\\\/]+'
SERIES_TITLE_PATTERN='^.*%s.*$'


class EpisodeMatch():
    def __init__(self, file_name, series, debug, season_number, episode_number):
        self.file_name = file_name
        self.series = series
        self.debug = debug

        self.season_number = season_number
        self.episode_number = episode_number

    def get_episode_metadata(self, database, thetvdb):
        episode = database.get_episode(self.series.id, self.season_number, self.episode_number)
        if episode is None:
            episode = thetvdb.get_specific_episode(self.series, self.season_number, self.episode_number)
            if episode is None:
                if self.debug:
                    print "Season %i episode %i of series '%s' does not exist.\n" % (self.season_number, self.episode_number, self.series.title)
                return None
            else:
                database.add_episode(episode, self.series)

        return episode


class DateMatch():
    def __init__(self, file_name, series, debug, year, month, day):
        self.file_name = file_name
        self.series = series
        self.debug = debug

        self.year = year
        self.month = month
        self.day = day

    def get_episode_metadata(self, database, thetvdb):
        episode = database.get_episode_by_date(self.series.id, self.year, self.month, self.day)
        if episode is None:
            episode = thetvdb.get_specific_episode_by_date(self.series, self.year, self.month, self.day)
            if episode is None:
                if self.debug:
                    print "No episode of series '%s' was originally aired on %i-%i-%i.\n" % (self.series.title, self.year, self.month, self.day)
                return None
            else:
                database.add_episode(episode, self.series)

        return episode


class FileMatcher():
    def __init__(self, config, series, debug):
        self.config = config
        self.series = series
        self.debug = debug

        series_title_pattern = self.build_series_title_pattern()
        self.series_title_re = self.compile(series_title_pattern)

        self.episode_re = self.compile(FILE_PATTERN_BY_EPISODE)
        self.episode_by_folder_re = self.compile(FILE_PATTERN_BY_EPISODE_FOLDERS)
        self.episode_by_date_re = self.compile(FILE_PATTERN_BY_DATE)

    def compile(self, pattern):
        return re.compile(pattern, re.IGNORECASE)

    def build_series_title_pattern(self):
        filtered_title = self.series.title
        chars_to_ignore = self.config.getTitleCharsToIgnore()
        words_to_ignore = self.config.getTitleWordsToIgnore()

        for c in chars_to_ignore:
            filtered_title = filtered_title.replace(c, ' ')

        split_title = [w.strip().lower() for w in filtered_title.split(' ')]

        split_filtered_title = []
        for tword in split_title:
            if not tword in words_to_ignore:
                split_filtered_title.append(tword)

        series_name_pattern = SERIES_TITLE_SEPARATOR_PATTERN.join(split_filtered_title)
        return SERIES_TITLE_PATTERN % (series_name_pattern, )


    def matches_series_title(self, file_path):
        match = self.series_title_re.match(file_path)
        if match:
            return True
        else:
            return False

    def match_episode(self, file_path):
        #return a list of matches
        to_return = []

        (dir_name, file_name) = os.path.split(file_path)
        dir_name=dir_name.replace('\\', '/')
        converted_file_name = dir_name + '/' + file_name

        # First try to match by season and episode number
        match = self.episode_re.match(file_name)
        
        # If we don't match the first episode pattern, try the folder version
        if not match:
            match = self.episode_by_folder_re.match(converted_file_name)

        if match:
            season_num = int(match.group('season'))
            episode_num = int(match.group('episode'))
            to_return.append(EpisodeMatch(file_path, self.series, self.debug, season_num, episode_num))

        # If that fails to match, try matching by date
        match = self.episode_by_date_re.match(file_name)
        if match:
            if not match.group('year1') is None:
                year = self.get_four_digit_year(int(match.group('year1')))
                month = int(match.group('month1'))
                day = int(match.group('day1'))
            else:
                year = self.get_four_digit_year(int(match.group('year2')))
                month = int(match.group('month2'))
                day = int(match.group('day2'))

            to_return.append(DateMatch(file_path, self.series, self.debug, year, month, day))

        return to_return


    def get_four_digit_year(self, raw_year):
        if raw_year > 99:
            return raw_year
        elif raw_year > 40:
            return raw_year + 1900
        else:
            return raw_year + 2000



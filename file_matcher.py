import re

DATE_PATTERN_1='(?P<month1>\d\d)[/-_.](?P<day1>\d\d)[/-_.](?P<year1>\d\d(\d\d)?)'
DATE_PATTERN_2='(?P<year2>\d\d\d\d)[/-_.](?P<month2>\d\d)[/-_.](?P<day2>\d\d)'

FILE_PATTERN_BY_EPISODE='^.*s(?P<season>\d+)[-_x\.\ ]?e(?P<episode>\d+).*$'
FILE_PATTERN_BY_EPISODE_FOLDERS='^.*/+season[-_.\ ]*(?P<season>\d+)/+(episode[-_.\ ]*)*(?P<episode>\d+).*$'
FILE_PATTERN_BY_DATE='^.*\D(' + DATE_PATTERN_1 + '|' + DATE_PATTERN_2 + ')\D.*$'

SERIES_TITLE_SEPARATOR_PATTERN='[^\\\/]+'

class EpisodeMatch():
    def __init__(self, season_number, episode_number):
        self.season_number = season_number
        self.episode_number = episode_number

class DateMatch():
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

class FileMatcher():
    def __init__(self, config, series_title):
        self.config = config
        self.series_title = series_title

        self.series_title_re = compile(self.build_series_title_pattern())
        self.episode_re = compile(FILE_PATTERN_BY_EPISODE)
        self.episode_by_folder_re = compile(FILE_PATTERN_BY_EPISODE_FOLDERS)
        self.episode_by_date_re = compile(FILE_PATTERN_BY_DATE)

    def compile(self, pattern):
        return re.compile(pattern, re.IGNORECASE)

    def build_series_title_pattern(self):
        filtered_title = self.series_title
        chars_to_ignore = self.config.getTitleCharsToIgnore()
        words_to_ignore = self.config.getTitleWordsToIgnore()

        for c in chars_to_ignore:
            filtered_title = filtered_title.replace(c, ' ')

        split_title = [w.strip().lower() for w in filtered_title.split(' ')]

        split_filtered_title = []
        for tword in split_title:
            if not tword in words_to_ignore:
                split_filtered_title.append(tword)

        return SERIES_TITLE_SEPARATOR_PATTERN.join(split_filtered_title)


    def matches_series_title(self, file_path):
        match = self.series_title_re.match(file_path)
        if match:
            return True
        else:
            return False

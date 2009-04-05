import sqlite3

from datetime import datetime

import config
import metadata

SERIES_COLUMNS="s.id, s.zap2it_id, s.imdb_id, s.title, s.description, s.actors, s.genres, s.content_rating, s.watch"
EPISODE_COLUMNS="e.id, e.title, e.description, e.season_number, e.episode_number, e.original_air_date, e.rating, e.director, e.host, e.choreographer, e.guest_stars, e.writers, e.executive_producers, e.producers"
MOVIE_COLUMNS="m.id, m.imdb_id, m.title, m.description, m.time, m.rating, m.directors, m.writers, m.producers, m.actors, m.movie_year, m.mpaa_rating, m.genres"

TIME_FORMAT='%Y-%m-%d %H:%M:%S'
ORIGINAL_AIR_DATE_FORMAT='%Y-%m-%d'

class Database():
    def __init__(self, config, debug):
        self.debug = debug

        database_file = config.getDatabaseFile()
        self.connection = sqlite3.connect(database_file)
        #self.connection.text_factory = sqlite3.OptimizedUnicode


    def get_series(self, id):
        c = self.connection.cursor()
        try:
            sql = 'select %s from series s where id=?' % (SERIES_COLUMNS, )
            c.execute(sql, (id, ))

            results = c.fetchall()
            if len(results) == 1:
                r = results[0]
                to_return = self.create_series_from_row(r)
                return to_return
            else:
                return None

        finally:
            c.close()

    def get_all_series(self):
        c = self.connection.cursor()
        try:
            sql = 'select %s from series s' % (SERIES_COLUMNS, )
            c.execute(sql)

            to_return = []
            results = c.fetchall()
            for r in results:
                to_return.append(self.create_series_from_row(r))

            return to_return

        finally:
            c.close()

    def add_series(self, series):
        existing_series = self.get_series(series.id)
        if existing_series is None:
            if self.debug:
                print "Adding series '%s' to the local cache." % (series.title, )

            c = self.connection.cursor()
            try:
                if series.watch:
                    watch = 1
                else:
                    watch = 0

                c.execute(
                        'insert into series (id, zap2it_id, imdb_id, title, description, actors, genres, content_rating, watch) values (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                        (series.id, series.zap2it_id, series.imdb_id, series.title, series.description, '|'.join(series.actors), '|'.join(series.genres), series.content_rating, watch))

                self.connection.commit()
            finally:
                c.close()
                

    def watch_series(self, series, watch):
        existing_series = self.get_series(series.id)
        if not existing_series is None:
            c = self.connection.cursor()
            try:
                if watch:
                    db_watch = 1
                else:
                    db_watch = 0

                c.execute(
                        'update series set watch = ? where id = ?', 
                        (db_watch, series.id))

                self.connection.commit()
            finally:
                c.close()

            if watch:
                print "Will now watch series '%s'." % (series.title, )
            else:
                print "Will no longer watch series '%s'." % (series.title, )

    def get_watched_series(self):
        c = self.connection.cursor()
        try:
            sql = 'select %s from series s where watch=1 order by title' % (SERIES_COLUMNS, )
            c.execute(sql)

            to_return = []

            results = c.fetchall()
            for r in results:
                to_return.append(self.create_series_from_row(r))

            return to_return

        finally:
            c.close()


    def clear_series(self, series_id):
        c = self.connection.cursor()
        try:
            sql = 'delete from series where id=?'
            c.execute(sql, (series_id, ))

            self.connection.commit()
        finally:
            c.close()





    def add_episode(self, episode, series):
        if self.debug:
            print "Adding season %i episode %i of series '%s' to the local cache." % (episode.season_number, episode.episode_number, series.title)

        c = self.connection.cursor()
        try:
            directors = '|'.join(episode.directors)
            guest_stars = '|'.join(episode.guest_stars)
            writers = '|'.join(episode.writers)
            executive_producers = '|'.join(episode.executive_producers)
            producers = '|'.join(episode.producers)

            if episode.original_air_date is None:
                original_air_date = ''
            else:
                original_air_date = episode.original_air_date.strftime(ORIGINAL_AIR_DATE_FORMAT)

            sql = 'insert into episodes '
            sql = sql + '(series_id, title, description, season_number, episode_number, '
            sql = sql + ' original_air_date, rating, director, host, choreographer, '
            sql = sql + ' guest_stars, writers, executive_producers, producers)'
            sql = sql + 'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            c.execute(sql, 
                    (series.id, episode.title, episode.description, episode.season_number,
                        episode.episode_number, original_air_date,
                        episode.rating, directors, episode.host, episode.choreographer, 
                        guest_stars, writers, executive_producers, producers))

            self.connection.commit()
        finally:
            c.close()


    def clear_all_episodes(self, series_id):
        c = self.connection.cursor()
        try:
            sql = 'delete from episodes where series_id=?'
            c.execute(sql, (series_id, ))

            self.connection.commit()
        finally:
            c.close()



    def get_all_episodes(self, series_id):
        c = self.connection.cursor()
        try:
            sql = 'select %s, %s from episodes e join series s on e.series_id = s.id where s.id=?' % (SERIES_COLUMNS, EPISODE_COLUMNS, )
            c.execute(sql, (series_id, ))

            results = c.fetchall()
            to_return = []
            for r in results:
                to_return.append(self.create_episode_from_row(r))

            return to_return
        finally:
            c.close()


    def get_episodes(self, series_id, season_number):
        c = self.connection.cursor()
        try:
            sql = 'select %s, %s from episodes e join series s on e.series_id = s.id where s.id=? and e.season_number=?' % (SERIES_COLUMNS, EPISODE_COLUMNS, )
            c.execute(sql, (series_id, season_number))

            results = c.fetchall()
            to_return = []
            for r in results:
                to_return.append(self.create_episode_from_row(r))

            return to_return
        finally:
            c.close()


    def get_episode(self, series_id, season_number, episode_number):
        c = self.connection.cursor()
        try:
            sql = 'select %s, %s from episodes e join series s on e.series_id = s.id where s.id=? and e.season_number=? and e.episode_number=?' % (SERIES_COLUMNS, EPISODE_COLUMNS, )
            c.execute(sql, (series_id, season_number, episode_number))

            results = c.fetchall()
            if len(results) == 1:
                to_return = self.create_episode_from_row(results[0])
                return to_return
            else:
                return None

        finally:
            c.close()


    def get_episode_by_date(self, series_id, year, month, day):
        the_date = datetime(year, month, day)
        the_date_str = the_date.strftime(ORIGINAL_AIR_DATE_FORMAT)

        c = self.connection.cursor()
        try:
            sql = 'select %s, %s from episodes e join series s on e.series_id = s.id where s.id=? and e.original_air_date=?' % (SERIES_COLUMNS, EPISODE_COLUMNS, )
            c.execute(sql, (series_id, the_date_str))

            results = c.fetchall()
            if len(results) == 1:
                to_return = self.create_episode_from_row(results[0])
                return to_return
            else:
                return None

        finally:
            c.close()




    def get_movie(self, id):
        c = self.connection.cursor()
        try:
            sql = 'select %s from movies m where imdb_id=?' % (MOVIE_COLUMNS, )
            c.execute(sql, (id, ))

            results = c.fetchall()
            if len(results) == 1:
                r = results[0]
                to_return = self.create_movie_from_row(r)
                return to_return
            else:
                return None

        finally:
            c.close()


    def get_all_movies(self):
        c = self.connection.cursor()
        try:
            sql = 'select %s from movies m' % (MOVIE_COLUMNS, )
            c.execute(sql)

            to_return = []
            results = c.fetchall()
            for r in results:
                to_return.append(self.create_movie_from_row(r))

            return to_return

        finally:
            c.close()


    def add_movie(self, movie):
        existing_movie = self.get_movie(movie.id)
        if existing_movie is None:
            if self.debug:
                print "Adding movie '%s' to the local cache." % (movie.title, )

            c = self.connection.cursor()
            try:
                c.execute(
                        'insert into movies (imdb_id, title, description, time, rating, directors, writers, producers, actors, movie_year, mpaa_rating, genres) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                        (movie.id, movie.title, movie.description, movie.time, movie.rating, '|'.join(movie.directors), '|'.join(movie.writers), '|'.join(movie.producers), '|'.join(movie.actors), movie.movie_year, movie.mpaa_rating, '|'.join(movie.genres)))

                self.connection.commit()
            finally:
                c.close()
             

    def clear_movie(self, movie_id):
        c = self.connection.cursor()
        try:
            sql = 'delete from movies where imdb_id=?'
            c.execute(sql, (movie_id, ))

            self.connection.commit()
        finally:
            c.close()










    def create_series_from_row(self, row):
        to_return = metadata.Series()
        to_return.id = row[0]
        to_return.zap2it_id = row[1]
        to_return.imdb_id = row[2]
        to_return.title = row[3]
        to_return.description = row[4]
        to_return.actors = row[5].split('|')
        to_return.genres = row[6].split('|')
        to_return.content_rating = row[7]
        if row[8] == 1:
            to_return.watch = True
        else:
            to_return.watch = False

        return to_return


    def create_episode_from_row(self, row):
        to_return = metadata.Episode()
        to_return.series = self.create_series_from_row(row)

        to_return.db_id = row[9]
        to_return.title = row[10]
        to_return.description = row[11]
        to_return.season_number = row[12]
        to_return.episode_number = row[13]
        if not row[14].strip() == '':
            to_return.original_air_date = self.get_datetime_from_string(row[14], ORIGINAL_AIR_DATE_FORMAT)
        else:
            to_return.original_air_date = None
        to_return.rating = row[15]
        to_return.directors = row[16].split('|')
        to_return.host = row[17]
        to_return.choreographer = row[18]
        to_return.guest_stars = row[19].split('|')
        to_return.writers = row[20].split('|')
        to_return.executive_producers = row[21].split('|')
        to_return.producers = row[22].split('|')

        return to_return

    def create_movie_from_row(self, row):
        to_return = metadata.Movie()

        to_return.db_id = row[0]
        to_return.id = row[1]
        to_return.title = row[2]
        to_return.description = row[3]
        if not row[4].strip() == '':
            to_return.time = self.get_datetime_from_string(row[4], TIME_FORMAT)
        else:
            to_return.time = None
        to_return.rating = row[5]
        to_return.directors = row[6].split('|')
        to_return.writers = row[7].split('|')
        to_return.producers = row[8].split('|')
        to_return.actors = row[9].split('|')
        to_return.movie_year = row[10]
        to_return.mpaa_rating = row[11]
        to_return.genres = row[12].split('|')

        return to_return



    def get_datetime_from_string(self, input_str, format):
        if input_str is None or input_str == '':
            return None
        else:
            return datetime.strptime(input_str, format)


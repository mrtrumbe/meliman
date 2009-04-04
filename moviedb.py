#! /usr/bin/env python

import imdb

from metadata import Movie

class MovieDB:
    def __init__(self, config, debug):
        self.debug = debug
        self.db = None

    def connect(self):
        if self.db is None:
            self.db = imdb.IMDb()


    def lookup_movie(self, search_text):
        self.connect()

        mlist = self.db.search_movie(seearch_text)

        # Assume its the first movie...if it isn't
        # the user needs to provide a better search string
        movie = mlist[0]

        to_return = Movie()
        to_return.id = self.get_id(movie)
        to_return.title = self.get_title(movie)
        to_return.description = self.get_plot(movie)
        to_return.movie_year = self.get_movie_year(movie)
        to_return.writers = self.get_writers(movie)
        to_return.actors = self.get_actors(movie)
        to_return.directors = self.get_directors(movie)
        to_return.producers = self.get_producers(movie)
        to_return.genres = self.get_genres(movie)
        to_return.rating = self.get_rating(movie)
        to_return.mpaa_rating = self.get_mpaa_rating(movie)
        
        return to_return


    # Private methods for extraction of information

    def get_id(self, movie):
        return int(self.db.get_imdbID(movie))

    def get_title(self, movie):
        return movie['title']

    def get_plot(self, movie):
        plot = movie['plot'][0]
        author_location = plot.rfind('::')

        to_return = plot
        if author_location > 0:
            to_return = plot[0:author_location]

        return to_return

    def get_movie_year(self, movie):
        return movie['year']

    def get_writers(self, movie):
        return [ w['name'] for w in movie['writer'] ]

    def get_actors(self, movie):
        return [ a['name'] for a in movie['actors'] ]

    def get_directors(self, movie):
        return [ d['name'] for d in movie['director'] ]

    def get_producers(self, movie):
        return [ p['name'] for p in movie['producer'] ]

    def get_genres(self, movie):
        return movie['genre']

    def get_rating(self, movie):
        return movie['rating']

    def get_mpaa_rating(self, movie):
        for c in movie['certificates']:
            split_c = c.split(':')
            if split_c[0] == 'USA':
                return split_c[1]

        return ''






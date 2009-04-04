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


    # Returns all movies matching the search_text,
    #  but only the summary data (id, title, year, etc.)
    def lookup_movies(self, search_text):
        self.connect()

        mlist = self.db.search_movie(search_text)
        to_return = []
        for m in mlist:
            #self.db.update(m)
            to_return.append(self.construct_movie_metadata(m))

        return to_return


    # Returns the movie best matching the search text
    #   Using the exact name and including the year
    #   helps search results
    def lookup_movie(self, search_text):
        self.connect()

        mlist = self.db.search_movie(search_text)

        # Assume its the first movie...if it isn't
        # the user needs to provide a better search string
        if len(mlist) == 0:
            return None

        movie = mlist[0]
        self.db.update(movie)

        return self.construct_movie_metadata(movie)


    def construct_movie_metadata(self, movie):
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
        return movie['title'].encode("utf-8")

    def get_plot(self, movie):
        try:
            plot = movie['plot'][0]
            author_location = plot.rfind('::')

            to_return = plot
            if author_location > 0:
                to_return = plot[0:author_location]

            return to_return.encode("utf-8")
        except:
            return ''

    def get_movie_year(self, movie):
        return int(movie['year'])

    def get_writers(self, movie):
        try:
            return [ w['name'].encode("utf-8") for w in movie['writer'] ]
        except:
            return []

    def get_actors(self, movie):
        try:
            return [ a['name'].encode("utf-8") for a in movie['actors'] ]
        except:
            return []

    def get_directors(self, movie):
        try:
            return [ d['name'].encode("utf-8") for d in movie['director'] ]
        except:
            return []

    def get_producers(self, movie):
        try:
            return [ p['name'].encode("utf-8") for p in movie['producer'] ]
        except:
            return []

    def get_genres(self, movie):
        try:
            return [ g.encode("utf-8") for g in movie['genre'] ]
        except:
            return []

    def get_rating(self, movie):
        try:
            return float(movie['rating'])
        except:
            return ''

    def get_mpaa_rating(self, movie):
        try:
            for c in movie['certificates']:
                split_c = c.split(':')
                if split_c[0] == 'USA':
                    return split_c[1].encode("utf-8")

            return ''
        except:
            return ''






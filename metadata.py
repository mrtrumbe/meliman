from datetime import datetime

class MetaData:

    def __init__(self):
        self.db_id = 0
        self.title = ""
        self.description = ""

        self.time = datetime(1900, 1, 1, 0, 0, 0)
        self.rating = 0.0

        self.host = ""
        self.choreographer = ""

        self.directors = []
        self.guest_stars = []
        self.writers = []
        self.executive_producers = []
        self.producers = []


class Series:

    def __init__(self):
        self.id = 0
        self.db_id = 0
        self.title = ""
        self.description = ""
        self.zap2it_id = ""

        self.watch = False

        self.actors = []
        self.genres = []
        self.content_rating = ""


class Episode(MetaData):
    
    def __init__(self):
        MetaData.__init__(self)

        self.series = Series()

        self.season_number = 0
        self.episode_number = 0

        self.original_air_date = datetime(1900, 1, 1, 0, 0, 0)

    def format_for_pyTivo(self, time_recorded):
        to_return = []

        # Episode info

        to_return.append('isEpisode : true')
        to_return.append('title : %s' % self.title, )
        to_return.append('time : %s' % time_recorded.strftime('%Y-%m-%dT%H:%M:%SZ'), )

        desc_out = 'description: #%i.  %s' % (self.episode_number, self.description.replace('\n', ' '))
        to_return.append(desc_out)

        if not self.original_air_date is None:
            to_return.append('originalAirDate : %s' % self.original_air_date.strftime('%Y-%m-%dT%H:%M:%SZ'), )

        if not (self.host is None or self.host == ''):
            to_return.append('vHost : %s' % self.host, )

        if not (self.choreographer is None or self.choreographer == ''):
            to_return.append('vChoreographer : %s' % self.choreographer, )

        for d in self.directors:
            if not (d is None or d.strip() == ''):
                to_return.append('vDirector : %s' % d, )

        for g in self.guest_stars:
            if not (g is None or g.strip() == ''):
                to_return.append('vGuestStar : %s' % g, )

        for w in self.writers:
            if not (w is None or w.strip() == ''):
                to_return.append('vWriter : %s' % w, )

        for e in self.executive_producers:
            if not (e is None or e.strip() == ''):
                to_return.append('vExecProducer : %s' % e, )

        for p in self.producers:
            if not (p is None or p.strip() == ''):
                to_return.append('vProducer : %s' % p, )

        ten_star_rating = self.rating
        eight_star_rating = 8 * ten_star_rating / 10.0
        four_star_rating = round(eight_star_rating) / 2.0
        tivo_star_rating = int(four_star_rating * 2) - 1
        if tivo_star_rating >= 1:
            to_return.append('starRating : x%i' % tivo_star_rating)

        # Series info

        to_return.append('seriesTitle : %s' % self.series.title, )

        if not (self.series.zap2it_id is None or self.series.zap2it_id == ''):
            to_return.append('seriesId : %s' % self.series.zap2it_id, )

        if not (self.series.content_rating is None or self.series.content_rating == ''):
            content_rating = self.series.content_rating
            tvRating = 'x0'

            if content_rating == 'TV-Y7':
                tvRating = 'x1'
            elif content_rating == 'TV-Y':
                tvRating = 'x2'
            elif content_rating == 'TV-G':
                tvRating = 'x3'
            elif content_rating == 'TV-PG':
                tvRating = 'x4'
            elif content_rating == 'TV-14':
                tvRating = 'x5'
            elif content_rating == 'TV-MA':
                tvRating = 'x6'
            elif content_rating == 'TV-NR':
                tvRating = 'x7'

            to_return.append('tvRating : %s' % tvRating, )

        for a in self.series.actors:
            if not (a is None or a.strip() == ''):
                to_return.append('vActor : %s' % a, )

        for g in self.series.genres:
            if not (g is None or g.strip() == ''):
                to_return.append('vProgramGenre : %s' % g, )


        return to_return

        


class Movie(MetaData):
    
    def __init__(self):
        MetaData.__init__(self)

        self.actors = []
        self.movie_year = 1900
        self.mpaa_rating = ""


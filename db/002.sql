create table series
    (
        id integer unique, 
        zap2it_id text, 
        imdb_id text,

        title text, 
        description text,

        actors text,
        genres text,
        content_rating text,

        watch int
    );

create table episodes
    (
        id integer primary key, 
        series_id integer references series (id), 
        title text, 
        description text, 
        season_number int, 
        episode_number int, 
        original_air_date text, 
        rating real, 
        director text, 
        host text, 
        choreographer text, 
        guest_stars text, 
        writers text, 
        executive_producers text, 
        producers text
    );

create table movies
    (
        id integer primary key, 
        imdb_id text, 
        title text, 
        description text, 
        season_number int, 
        episode_number int, 
        movie_year int, 
        rating real, 
        mpaa_rating text, 
        director text, 
        choreographer text, 
        actors text, 
        writers text, 
        executive_producers text, 
        producers text
    );

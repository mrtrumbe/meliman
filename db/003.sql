drop table movies;

create table movies
    (
        id integer primary key,
        imdb_id int unique,
        title text,
        description text,
        time text,
        rating real,
        directors text,
        writers text,
        producers text,
        actors text,
        movie_year int,
        mpaa_rating text,
        genres text
    );

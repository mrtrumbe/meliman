#!/bin/bash

scriptPath="${0%/*}"

mkdir -p "$scriptPath/../tmp/tv"
mkdir -p "$scriptPath/../tmp/movies"
mkdir -p "$scriptPath/../tmp/input"
mkdir -p "$scriptPath/../tmp/movie_input"
mkdir -p "$scriptPath/../tmp/recent"

cp "$scriptPath/../meliman.conf.dist" "$scriptPath/../meliman.conf"

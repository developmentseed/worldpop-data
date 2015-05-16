#!/usr/bin/env bash

mkdir -p temp
mkdir -p shapes
mkdir -p tiles

parallel scripts/vectorize.sh {} 1 density shapes <&0

scripts/setup-pg.sh
ls shapes/*.shp | scripts/merge.sh population
ls shapes/coverage/*.shp | scripts/merge.sh coverage

psql -d worldpop -f scripts/simplify.sql


#!/usr/bin/env bash

if [[ $# -le 1 ]] ; then
  echo "Usage: $0 inputfile.tif database_name"
  exit 0
fi

raster2pgsql -N 0 $1 public.pop > temp/out.sql
psql -d $2 -f temp/out.sql

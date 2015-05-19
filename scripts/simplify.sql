DROP TABLE coverage_005;
CREATE TABLE coverage_005 () WITH ( OIDS=FALSE );
SELECT AddGeometryColumn('public', 'coverage_005', 'wkb_geometry', 4326, 'POLYGON', 2);

INSERT INTO coverage_005
  (SELECT ST_AsEWKB(ST_Simplify(ST_GeomFromEWKB(wkb_geometry), 0.05))
    as wkb_geometry FROM coverage);

CREATE INDEX coverage_01_wkb_geometry_geom_idx
  ON public.coverage_005 USING gist (wkb_geometry);


DROP TABLE population_005;
CREATE TABLE population_005 (density numeric(10)) WITH ( OIDS=FALSE );
SELECT AddGeometryColumn('public', 'population_005', 'wkb_geometry', 4326, 'POLYGON', 2);

INSERT INTO population_005
(SELECT
  density,
  ST_AsEWKB(ST_Simplify(ST_GeomFromEWKB(wkb_geometry), 0.05)) as wkb_geometry
  FROM population);

CREATE INDEX population_005_wkb_geometry_geom_idx
  ON public.population_005 USING gist (wkb_geometry);


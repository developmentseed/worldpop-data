DROP TABLE coverage_001;
CREATE TABLE coverage_001 () WITH ( OIDS=FALSE );
SELECT AddGeometryColumn('public', 'coverage_001', 'wkb_geometry', 4326, 'POLYGON', 2);

INSERT INTO coverage_001
  (SELECT ST_AsEWKB(ST_Simplify(ST_GeomFromEWKB(wkb_geometry), 0.01))
    as wkb_geometry FROM coverage);

CREATE INDEX coverage_001_wkb_geometry_geom_idx
  ON public.coverage_001 USING gist (wkb_geometry);

import csv
import json
import logging
import pathlib
import sys

import fiona
import numpy
import rasterio
import shapely
import tqdm
from rasterio.warp import transform_geom

datasets = {
    "sd": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_snow/sd/sd_{year}.nc:snow_depth",
    "rr": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_{year}.nc:rr",
    "tg": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_{year}.nc:tg",
}

logging.basicConfig(level=logging.INFO)


def main(vector_path, year, layers) -> None:
    logging.debug("Opening vector...")
    vector = fiona.open(vector_path)

    logging.info("Loading geometries...")
    points = []
    for element in vector:
        centroid = shapely.geometry.shape(element["geometry"]).centroid
        points.append(json.loads(shapely.to_geojson(centroid)))

    samples = []
    for topic in tqdm.tqdm(layers, unit="layer"):
        dataset = rasterio.open(datasets[topic].format(year=year))
        transformed = transform_geom(vector.crs, dataset.crs, points)
        coordinates = (point["coordinates"] for point in transformed)
        samples.append(list(dataset.sample(coordinates)))

    samples = numpy.array(samples)
    samples = samples.swapaxes(0, 1)
    samples = samples.swapaxes(1, 2)

    with pathlib.Path(f"{year}.csv").open("w") as csvfile:
        csvwriter = csv.writer(csvfile, dialect="excel")
        csvwriter.writerow(("x", "y", "year", "day", *layers))
        for point, sample in zip(points, samples, strict=False):
            for day, values in enumerate(sample):
                csvwriter.writerow((*point["coordinates"], year, day, *values))


def cli() -> None:
    main(vector_path=sys.argv[1], year=sys.argv[2], layers=sys.argv[3:])


if __name__ == "__main__":
    cli()

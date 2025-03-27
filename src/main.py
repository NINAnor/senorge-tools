import csv
import json
import pathlib
import sys

import fiona
import rasterio
import shapely
from rasterio.warp import transform_geom

datasets = {
    "sd": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_snow/sd/sd_{year}.nc:snow_depth",
    "lwc": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_snow/lwc/lwc_{year}.nc:snow_liquid_water_content",
    "rr": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_{year}.nc:rr",
    "tn": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_{year}.nc:tn",
    "tg": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_{year}.nc:tg",
    "tx": "NETCDF:/vsicurl/https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_{year}.nc:tx",
}


def main(vector_path, layer, year) -> None:
    with fiona.open(vector_path) as vector:
        points = []
        for feature in vector:
            centroid = shapely.geometry.shape(feature.geometry).centroid
            points.append(json.loads(shapely.to_geojson(centroid)))

        dataset = rasterio.open(datasets[layer].format(year=year))
        transformed = transform_geom(vector.crs, dataset.crs, points)
        coordinates = (point["coordinates"] for point in transformed)
        samples = dataset.sample(coordinates)

        header = [
            "row_number",
            "x",
            "y",
            "year",
            "day",
            "layer",
            "value",
        ]
        with pathlib.Path(f"{layer}_{year}.csv").open("w") as csvfile:
            csvwriter = csv.writer(csvfile, dialect="excel")
            csvwriter.writerow(header)
            for index, (point, sample) in enumerate(zip(points, samples, strict=True)):
                for day, value in enumerate(sample):
                    csvwriter.writerow(
                        (
                            index + 1,
                            *point["coordinates"],
                            year,
                            day,
                            layer,
                            value,
                        )
                    )


def cli() -> None:
    main(vector_path=sys.argv[1], layer=sys.argv[2], year=sys.argv[3])


if __name__ == "__main__":
    cli()

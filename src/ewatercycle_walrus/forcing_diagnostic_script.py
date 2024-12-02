"""WALRUS diagnostic."""
import csv
import logging
from pathlib import Path

import iris
import pandas as pd
import xarray as xr

from esmvalcore import preprocessor as preproc
from esmvaltool.diag_scripts.hydrology.derive_evspsblpot import debruin_pet
from esmvaltool.diag_scripts.shared import (
    ProvenanceLogger,
    get_diagnostic_filename,
    group_metadata, run_diagnostic
)

logger = logging.getLogger(Path(__file__).name)


def create_provenance_record():
    """Create a provenance record."""
    record = {
        'caption': "Forcings for the WALRUS hydrological model.",
        'domains': ['global'],
        'authors': [],
        'projects': [
            'ewatercycle',
        ],
        'references': [
            'acknow_project',
        ],
        'ancestors': [],
    }
    return record


def get_input_cubes(metadata):
    """Return a dict with all (preprocessed) input files."""
    provenance = create_provenance_record()
    all_vars = {}
    for attributes in metadata:
        short_name = attributes['short_name']
        if short_name in all_vars:
            raise ValueError(
                f"Multiple input files found for variable '{short_name}'.")
        filename = attributes['filename']
        logger.info("Loading variable %s", short_name)
        all_vars[short_name] = iris.load_cube(filename)
        provenance['ancestors'].append(filename)
    return all_vars, provenance


def _get_extra_info(cube):
    """Get start/end time and origin of cube.

    Get the start and end times as an array with length 6
    and get latitude and longitude as an array with length 2
    """
    coord = cube.coord('time')
    time_start_end = []
    for index in 0, -1:
        time_val = coord.cell(index).point
        time_val = [
            time_val.year,
            time_val.month,
            time_val.day,
            time_val.hour,
            time_val.minute,
            time_val.second,
        ]
        time_val = [float(time) for time in time_val]
        time_start_end.append(time_val)

    # Add data_origin
    lat_lon = [
        cube.coord(name).points[0] for name in ('latitude', 'longitude')
    ]
    return time_start_end, lat_lon


def _shift_era5_time_coordinate(cube):
    """Shift instantaneous variables 30 minutes forward in time.

    After this shift, as an example:
    time format [1990, 1, 1, 11, 30, 0] will be [1990, 1, 1, 12, 0, 0].
    For aggregated variables, already time format is [1990, 1, 1, 12, 0, 0].
    """
    time = cube.coord(axis='T')
    time.points = time.points + 30 / (24 * 60)
    time.bounds = None
    time.guess_bounds()
    return cube


def main(cfg):
    """Process data for use as input to the WALRUS hydrological model.

    These variables are needed in all_vars:
    tas (air_temperature)
    pr (precipitation_flux)
    psl (air_pressure_at_mean_sea_level)
    rsds (surface_downwelling_shortwave_flux_in_air)
    rsdt (toa_incoming_shortwave_flux)
    """
    input_metadata = cfg['input_data'].values()
    for dataset, metadata in group_metadata(input_metadata, 'dataset').items():
        all_vars, provenance = get_input_cubes(metadata)

        # Fix time coordinate of ERA5 instantaneous variables
        if dataset == 'ERA5':
            _shift_era5_time_coordinate(all_vars['psl'])
            _shift_era5_time_coordinate(all_vars['tas'])

        # Processing variables and unit conversion
        # Unit of the fluxes in WALRUS should be in kg m-2 day-1 (or mm/day)
        logger.info("Processing variable PET")
        pet = debruin_pet(
            psl=all_vars['psl'],
            rsds=all_vars['rsds'],
            rsdt=all_vars['rsdt'],
            tas=all_vars['tas'],
        )
        pet = preproc.area_statistics(pet, operator='mean')
        pet.convert_units('kg m-2 day-1')  # equivalent to mm/day

        logger.info("Processing variable tas")
        temp = preproc.area_statistics(all_vars['tas'], operator='mean')
        temp.convert_units('celsius')

        logger.info("Processing variable pr")
        precip = preproc.area_statistics(all_vars['pr'], operator='mean')
        precip.convert_units('kg m-2 day-1')  # equivalent to mm/day

        dateindex = pd.DatetimeIndex(
            data=xr.DataArray.from_iris(temp)["time"].to_series(),
            name="date",
        )
        df_out = pd.DataFrame(
            data={
                "P": precip.data,
                "ETpot": pet.data,
            },
            index=dateindex.strftime("%Y%m%d%H").astype(int),
        )

        # Save to R-compatible .dat file
        basename = '_'.join([
            'WALRUS',
            dataset,
            cfg['basin'],
            str(df_out.index[0]),
            str(df_out.index[0]),
        ])
        output_name = get_diagnostic_filename(basename, cfg, extension='dat')
        df_out.to_csv(
            output_name,
            sep=" ",
            quoting=csv.QUOTE_NONNUMERIC,
        )

        # Store provenance
        with ProvenanceLogger(cfg) as provenance_logger:
            provenance_logger.log(output_name, provenance)


if __name__ == '__main__':

    with run_diagnostic() as config:
        main(config)

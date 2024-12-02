"""Forcing related functionality for WALRUS."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import xarray as xr

from ewatercycle.base.forcing import DefaultForcing
from ewatercycle.esmvaltool.builder import RecipeBuilder
from ewatercycle.esmvaltool.schema import Dataset, Recipe


class WALRUSForcing(DefaultForcing):
    """Container for WALRUS forcing data.

    Args:
        directory: Directory where forcing data files are stored.
        start_time: Start time of forcing in UTC and ISO format string e.g.
            'YYYY-MM-DDTHH:MM:SSZ'.
        end_time: End time of forcing in UTC and ISO format string e.g.
            'YYYY-MM-DDTHH:MM:SSZ'.
        shape: Path to a shape file. Used for spatial selection.
        forcing_file: .dat file that contains forcings for WALRUS
            models.

    Examples:

        From existing forcing data:

        .. code-block:: python

            from ewatercycle.forcing import sources

            forcing = sources.WALRUS(
                directory='/data/WALRUS-forcings-case1',
                start_time='1989-01-02T00:00:00Z',
                end_time='1999-01-02T00:00:00Z',
                forcing_file='WALRUS-1989-1999.dat'
            )

        Generate from ERA5 forcing dataset and Rhine.

        .. code-block:: python

            from ewatercycle.forcing import sources
            from ewatercycle.testing.fixtures import rhine_shape

            shape = rhine_shape()
            forcing = sources.WALRUSForcing.generate(
                dataset='ERA5',
                start_time='2000-01-01T00:00:00Z',
                end_time='2001-01-01T00:00:00Z',
                shape=shape,
            )
    """

    forcing_file: str = ""

    @classmethod
    def _build_recipe(
        cls,
        start_time: datetime,
        end_time: datetime,
        shape: Path,
        dataset: Dataset | str | dict,
        **model_specific_options,
    ):
        return build_walrus_recipe(
            start_year=start_time.year,
            end_year=end_time.year,
            shape=shape,
            dataset=dataset,
        )

    @classmethod
    def _recipe_output_to_forcing_arguments(cls, recipe_output, model_specific_options):
        # key in recipe_output is concat of dataset, shape start year and end year
        # for example 'WALRUS_ERA5_Rhine_2000_2001.dat'
        # instead of constructing key just use first and only value of dict
        first_forcing_file = next(iter(recipe_output.values()))
        return {"forcing_file": first_forcing_file}

    def to_xarray(self) -> xr.Dataset:
        """Load forcing data from a Matlab file into an xarray dataset.

        Returns:
            Dataset with forcing data.
        """
        if self.directory is None or self.forcing_file is None:
            raise ValueError("Directory or forcing_file is not set")
        fn = self.directory / self.forcing_file
        
        df = pd.read_csv(
            fn, sep=" ", index_col=0, parse_dates=[0],date_format="%Y%m%d%H"
        )

        # TODO use netcdf-cf conventions
        return xr.Dataset(
            {
                "precipitation": (
                    ["time"],
                    df["P"],
                    {"units": "mm/day"},
                ),
                "evspsblpot": (
                    ["time"],
                    df["ETpot"],
                    {"units": "mm/day"},
                ),
            },
            coords={
                "time": df.index,
            },
            attrs={
                "title": "WALRUS forcing data",
                "history": "Created by ewatercycle_walrus.forcing.WALRUSForcing.to_xarray()",
            },
        )


def build_walrus_recipe(
    start_year: int,
    end_year: int,
    shape: Path,
    dataset: Dataset | str | dict,
) -> Recipe:
    """Build an ESMValTool recipe for generating forcing for WALRUS.

    Args:
        start_year: Start year of forcing.
        end_year: End year of forcing.
        shape: Path to a shape file. Used for spatial selection.
        dataset: Dataset to get forcing data from.
            When string is given a predefined dataset is looked up in
            :py:const:`ewatercycle.esmvaltool.datasets.DATASETS`.
            When dict given it is passed to
            :py:class:`ewatercycle.esmvaltool.models.Dataset` constructor.
    """
    return (
        RecipeBuilder()
        .title("Generate forcing for the WALRUS hydrological model")
        .description("Generate forcing for the WALRUS hydrological model")
        .dataset(dataset)
        .start(start_year)
        .end(end_year)
        .shape(shape)
        # TODO do lumping in recipe preprocessor instead of in diagnostic script
        # .lump()
        .add_variables(("tas", "pr", "psl", "rsds"))
        .add_variable("rsdt", mip="CFday")
        .script(
            str((Path(__file__).parent / "forcing_diagnostic_script.py").absolute()),
            {"basin": shape.stem})
        .build()
    )

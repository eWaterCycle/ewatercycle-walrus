"""eWaterCycle wrapper for the LeakyBucket model."""
import yaml
from collections.abc import ItemsView
from pathlib import Path
from typing import Any, Literal
import numpy as np

from ewatercycle.base.model import ContainerizedModel, eWaterCycleModel
from ewatercycle.container import ContainerImage
from ewatercycle.util import get_time

from ewatercycle_walrus.forcing import WALRUSForcing


WALRUS_PARAMETERS = ["cW", "cV", "cG", "cQ", "cS", "dG0", "cD", "aS", "st"]


def datetime_to_float(dt) -> float:
    """Convert a datetime to an R floating point numer (hours since 1970)"""
    return float(np.datetime64(dt, "h").astype(float))


class WALRUSMethods(eWaterCycleModel):
    """The eWatercycle LeakyBucket model.
    
    Setup args:
        parameters: dictionary with the following parameters:
            cW: wetness index parameter (mm)
            cV: vadose zone relaxation time (h)
            cG: groundwater reservoir constant (mm h)
            cQ: quickflow reservoir constant (h)
            cS: bankfull discharge
            dG0: initial groundwater depth (mm)
            cD: channel depth (mm)
            aS: surface water area fraction (-)
            st: soil type
    
    Available soil types in WALRUS:
        "sand", "loamy_sand", "sandy_loam", "silt_loam", "loam", "sandy_clay_loam",
        "silt_clay_loam", "clay_loam", "sandy_clay", "silty_clay", "clay",
        "cal_H", "cal_C"
    """
    forcing: WALRUSForcing  # The model requires forcing.
    parameter_set: None  # The model has no parameter set.

    _config: dict = {
        "data": "",
        "parameters": {
            "cW": 200,
            "cV": 4,
            "cG": 5.0e6,
            "cQ": 10,
            "cS": 4,
            "dG0": 1250,
            "cD": 1500,
            "aS": 0.01,
            "st": "loamy_sand",
        },
        "start": 0,
        "end": 0,
        "step": 1,
    }

    def _make_cfg_file(self, **kwargs) -> Path:
        """Write model configuration file."""
        forcing_file = Path(self.forcing.forcing_file)
        if forcing_file.is_absolute():
            self._config["data"] = str(forcing_file)
        else:
            self._config["data"] = str(self.forcing.directory / forcing_file)

        # Get start/end
        forcing = self.forcing.to_xarray()
        if "start_time" in kwargs:
            self._config["start"] = datetime_to_float(get_time(kwargs["start_time"]))
        else:
            self._config["start"] = datetime_to_float(forcing["time"].to_numpy()[0])
        
        if "end_time" in kwargs:
            self._config["start"] = datetime_to_float(get_time(kwargs["end_time"]))
        else:
            self._config["end"] = datetime_to_float(forcing["time"].to_numpy()[-1])

        self._config["step"] = 1  # step in forcing table, seems to be bugged.
        # (
        #     datetime_to_float(forcing["time"].to_numpy()[1]) -
        #     datetime_to_float(forcing["time"].to_numpy()[0])
        # )

        if "parameters" in kwargs:
            params = kwargs["parameters"]
            if not isinstance(params, dict):
                msg = "keyword argument 'parameters' must be a dictionary!"
                raise ValueError(msg)
            if not all(p in params for p in WALRUS_PARAMETERS):
                missing = set(WALRUS_PARAMETERS) - set(params)
                msg = f"The following parameters are missing: {missing}"
                raise ValueError(msg)
            self._config["parameters"] = params

        config_file = self._cfg_dir / "walrus_config.yml"

        with config_file.open(mode="w") as f:
            f.write(yaml.dump(self._config))

        return config_file

    @property
    def parameters(self) -> ItemsView[str, Any]:
        return self._config.items()


class WALRUS(ContainerizedModel, WALRUSMethods):
    """The WALRUS eWaterCycle model, with the Container Registry docker image."""
    bmi_image: ContainerImage = ContainerImage(
        "ghcr.io/ewatercycle/ewatercycle-walrus:0.0.1"
    )
    protocol: Literal["grpc", "openapi"] = "openapi"

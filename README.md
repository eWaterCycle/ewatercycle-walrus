# eWaterCycle plugin for the WALRUS model

Note: the [WALRUS BMI](https://raw.githubusercontent.com/eWaterCycle/grpc4bmi-examples/master/walrus/walrus-bmi.r) 
is barely implemented and relies on "faking it"; `.update()` actually doesn't update the model:
it ran the entire simulation already on `.initialize()`.

This plugin is only to demonstrate communication between eWaterCycle and an R-based model inside a container.

## Installation

Install this package alongside your eWaterCycle installation

```console
pip install ewatercycle-walrus
```

Then WALRUS becomes available as one of the eWaterCycle models

```python
from ewatercycle.models import WALRUS
```

## License

`ewatercycle-walrus` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.

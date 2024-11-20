# Add your model to eWaterCycle

This document describes the steps to add a model plugin to eWaterCycle. For
general information about adding models to eWaterCycle, see the [eWaterCycle
documentation](https://ewatercycle.readthedocs.io/en/latest/adding_models.html)

**Table of Contents**
* [Prerequisites](#prerequisites)
  + [Basic Model Interface](#basic-model-interface)
  + [Container with grpc4bmi](#container-with-grpc4bmi)
* [Wrapping your model in the eWaterCycle interface](#wrapping-your-model-in-the-ewatercycle-interface)
  + [eWaterCycle Forcing](#ewatercycle-forcing)
  + [Registering your plugin](#registering-your-plugin)
  + [Update readme and demo notebook](#update-readme-and-demo-notebook)
  + [Upload to PyPI](#upload-to-pypi)
  + [Listing your plugin on the eWaterCycle documentation](#listing-your-plugin-on-the-ewatercycle-documentation)
* [Tips and tricks](#tips-and-tricks)
  + [Local Python model](#local-python-model)

## Prerequisites

You will need a model that:

- [exposes the Basic Model Interface](#basic-model-interface-bmi), and
- (ideally) is [packaged in a (docker/apptainer) container with grpc4bmi](#container-with-grpc4bmi)

### Basic Model Interface

The basic model interface is a set of standards that can be used to control
simulation models such as used in many earth system model components. It is
designed by CSDMS, and you can find more information on [their
website](https://bmi.readthedocs.io/en/stable/).

For example, (almost) every model has a main time loop, an initialization
routine, and an update function. By standardizing these, we can easily combine
or switch between different models:

```py
model.initialize()
while model.time < model.end_time:
    model.update()
```

The BMI is available in most languages used for earth system models. If you
already have a model, you need to wrap it in the BMI interface. Otherwise, you
can start from the simple leaky-bucket model that we've written especially for this
purpose: [leakybucket-bmi](https://github.com/eWaterCycle/leakybucket-bmi)

### Container with grpc4bmi

In eWaterCycle models are stored in (Docker) container images, which can be
shared through the Github Container Registry or DockerHub.

Besides the model code, the container image should install the grpc4bmi server
as an entrypoint to enable communication with the model from outside of the
container. We use standardized image names including a unique version number for
the model.

Concretely, these are the steps you should follow:

- Create Docker container image named `ewatercycle/<model>-grpc4bmi:<version>`
with grpc4bmi server running as entrypoint. For detailed instructions and
examples, please see the [grpc4bmi
docs](https://grpc4bmi.readthedocs.io/en/latest/container/building.html).
- Host Docker container image on the [Github
registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

Again, for an example see the
[leakybucket-bmi](https://github.com/eWaterCycle/leakybucket-bmi) repository,
which includes a Dockerfile.

> Note: if you have a Python BMI, you can use the model without a container for
> testing purposes, more info is available [down
> below](#local-python-model-no-container).

## Wrapping your model in the eWaterCycle interface

To be able to interface your model in eWaterCycle, you need to wrap it in an
eWaterCycle model class. The eWaterCycle wrapper adds some additional BMI
utilities that are relevant for hydrological models, and it can also combine the
'bare' BMI model with forcing data and parameter sets. It is modelled after
[PyMT](https://csdms.colorado.edu/wiki/PyMT), but additionally it can run BMI
models inside containers.

This model class will have to handle the forcing and/or parameter set input, as
well as the model configuration file.

It is stuctured like the following:

```py
from ewatercycle.base.model import ContainerizedModel, eWaterCycleModel

# This "methods" class implements the eWaterCycle interface, and can be reused.
class MyPluginMethods(eWaterCycleModel):
    forcing: GenericLumpedForcing  # Models usually require forcing.

    parameter_set: ParameterSet  # If the model has a parameter set

    _config: dict = {  # _config holds model configuration settings:
        "forcing_file": "",
        "model_setting_1": 0.05,
    }

    @model_validator(mode="after")
    def _update_config(self):
        ... # Update the config, e.g., by adding the forcing directory.
        return self

    def _make_cfg_file(self, **kwargs) -> Path:
        """Write model configuration file."""
        ... # Write the config to a file to pass it to your model BMI.

class MyModel(ContainerizedModel, MyPluginMethods):
    # The local model uses a local BMI class
    bmi_image: ContainerImage = ContainerImage(
        "ghcr.io/organization/model:v0.0.1"
    )
```

As a starting point, you can use the ewatercycle-leakybucket plugin from this
repo, following the steps outlined below.

1. Create a new repo, by pressing the "use this template" button on
   [ewatercycle-leakybucket
   repo](https://github.com/eWaterCycle/ewatercycle-leakybucket) or following
   [this
   link](https://github.com/new?template_name=ewatercycle-leakybucket&template_owner=eWaterCycle)
   In choosing a name for your plugin, please prepend `ewatercycle-`, e.g. for
   our model called leakybucket we used `ewatercycle-leakybucket`.
1. Replace all instances of "leakybucket"/"LeakyBucket" with your model name, including
   - `git mv src/ewatercycle_leakybucket/ src/ewatercycle_mymodel`
   - everything in `pyproject.toml`
   - everything in `src/ewatercycle_mymodel/model.py`
1. If necessary, update the version in `src/ewatercycle_mymodel/__init__.py`, for example when you want make the version of the plugin match the version of your model.
1. Remove this plugin guide from your copy of the repo: `git rm plugin_guide.md`
1. Update the code in `src/ewatercycle_mymodel` to your needs
1. Optional: [add forcing](#ewatercycle-forcing)
1. [Register and install your plugin](#registering-your-plugin)
1. [Update the readme and demo notebook](#update-readme-and-demo-notebook)
1. [Make your plugin available on PyPI](#upload-to-pypi)
1. [List your plugin on the eWaterCycle documentation](#listing-your-plugin-on-the-ewatercycle-documentation)
1. [Make your plugin citeable](https://zenodo.org/account/settings/github/)
1. Add tests and continuous integration

### eWaterCycle Forcing

For generating and loading model forcing, eWaterCycle makes use of a Forcing
class. When generating forcing, ESMValTool recipes are used. This allows for
standardized and reproducible forcing.

If you are making a new model, you can use the GenericForcing, which has a
lumped and a gridded version available.

If you are using an existing model that deviates from the standard forcing, you
can make your own custom forcing class. For more info on this, see [the
eWaterCycle documentation on
forcing.](https://ewatercycle.readthedocs.io/en/latest/user_guide.html#Forcing-data).

### Registering your plugin

eWaterCycle uses
[entrypoints](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-package-metadata)
to discover plugins installed in your environment. Making your plugin discoverable is done in the
`pyproject.toml` file:

```toml
# This registers the plugin such that it is discoverable by eWaterCycle
[project.entry-points."ewatercycle.models"]
MyModel = "mymodel.ewatercycle_model:MyModel"
```

Here you should have replaced the leaky bucket names with the correct model and class
name of your own model.

After (re-)installing your model (`pip install -e .`), you should be able to import and run your model in eWaterCycle:

```py
from ewatercycle.models import MyModel
```

Well done! 🚀

### Update readme and demo notebook

To help potential users find and use your plugin, it is imperative to have an
adequate readme and ship an example notebook with the repository that runs a
simple example case.

A working example notebook is a requirement for listing your plugin on the
eWaterCycle documentation.

You can use the [demo_containerized_model.ipynb](demo_containerized_model.ipynb) notebook as a starting point for a notebook that works with your model.

### Upload to PyPI

After finishing the previous steps, you should upload the finished package to
pypi.org. For information on packaging your project, see [the Python
documentation](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

This will allow others to install it into their eWaterCycle installation using
(for example):

```sh
pip install ewatercycle-mymodel
```

### Listing your plugin on the eWaterCycle documentation

eWaterCycle maintains a list of endorsed plugins [in its
documentation](https://ewatercycle.readthedocs.io/en/latest/plugins.html)

To get your model listed, you can [open a pull
request](https://github.com/eWaterCycle/ewatercycle/edit/main/docs/plugins.rst).

## Tips and tricks

### Local Python model

For testing purposes you can directly use a Python model's BMI in eWaterCycle.
For this you need to combine the eWaterCycle class methods with the eWaterCycle
LocalModel as such:

```py
from ewatercycle.base.model import LocalModel
from leakybucket import LeakyBucketBmi
from ewatercycle_leakybucket.model import LeakyBucketMethods

class LocalModelLeakyBucket(LocalModel, LeakyBucketMethods):
    """The LeakyBucket eWaterCycle model, with the local BMI."""
    bmi_class: Type[Bmi] = LeakyBucketBmi
```

Where LeakyBucketBmi is your local model's BMI class.

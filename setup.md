# Setup New Virtualenv
python -m pip install --upgrade pip

## Install nbdev
python -m pip install setuptools
python -m pip install nbdev

## Install ds_tut Package
python -m pip install black
nbdev_export
python -m pip install -e ".[dev]"

## quarto
nbdev_preview  # installs quarto the first time called

## jupyter
python -m pip install jupyterlab

# Run the Development-Environment
honcho start  # runs quarto + jupyterlab

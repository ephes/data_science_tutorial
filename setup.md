# New Virtualenv
python -m pip install --upgrade pip

python -m pip install setuptools
python -m pip install nbdev

python -m pip install black
nbdev_export
python -m pip install -e ".[dev]"

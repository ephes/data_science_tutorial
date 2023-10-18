# data_science_tutorial
Python data science and machine learning tutorial

# Installation

## Checkout the repository

```shell
git clone git@github.com:ephes/data_science_tutorial.git ds_tutorial
cd ds_tutorial
```

## Miniconda

To set up the environment you should at first install
[miniconda](https://conda.io/miniconda.html). And update it:

FIXME / TODO:
* maybe add a line about installing miniconda with pyenv?
* conda update -n base conda | does not work with pyenv..
  * It's fixed by: python -m pip install chardet
* conda init fish

```shell
conda update -n base conda
```

Then proceed to create the conda environment:

```shell
cd ds_tutorial
conda env create -f environment.yml
```

## Activate Environment

Activate ds_tutorial environment:
```shell
conda activate ds_tutorial
```

## Install ds_tutorial package

FIXME:
* probably not

```
pip install -e .
```

# Start notebook server

FIXME:
* no makefile

```shell
make notebook
```

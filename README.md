# data_science_tutorial
Python data science and machine learning tutorial

# Installation

## Checkout the repository

```shell
git clone git@github.com:ephes/data_science_tutorial.git ds_tutorial
```

## Miniconda

To set up the environment you should at first install
[miniconda](https://conda.io/miniconda.html). And update it:

```shell
conda update -n base conda
```

Then proceed to create the conda environment:

```shell
cd ds_tutorial
conda env create
```

## Activate Environment

Activate ds_tutorial environment:
```shell
conda activate ds_tutorial
```

## Install ds_tutorial package
```
pip install -e .
```

# Start notebook server

```shell
cd notebooks
jupyter notebook
```

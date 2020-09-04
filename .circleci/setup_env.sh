#!/bin/bash

apt-get update
apt-get install -y python-virtualenv curl build-essential gcc-4.8
apt-get install -y python-virtualenv
pip install -e git+https://github.com/eteq/nbpages.git@b9ec8410803357939210e068af7e14a6f0625fab#egg=nbpages
pip install -U pip jupyterlab

# conda info --envs
# conda env update --file=environment.yml
# source activate notebooks_env
# conda info --envs
# name: notebooks_env_two
# 
# channels:
#   - astropy
#   - http://ssb.stsci.edu/astroconda
#   - defaults
# 
# dependencies:
#   - python=3.7
#   - ca-certificates=2019.8.28
#   - pip
#   - virtualenv=16.0.0
#   - numpy=1.15.4
#   - astropy=3.0.4
#   - pip:
#     - future==0.17.1
#     - junitparser==1.3.4
#     - 
#     # Below is required by nbpages
#     - jupyter==1.0.0
#     - jupyter-client==5.3.3
#     - astroquery==0.3.10
#     - matplotlib>=2.2.2
#     - numpy>=1.15.4
#     - photutils>=0.6
#     - webbpsf>=0.8
#     - scikit-learn>=0.20
#     - k2flix>=2.4.0
#     - bokeh>=0.12.16
#     - pandas>=0.23.4
#     - ccdproc>=1.3.0
#     - drizzlepac>=2.2.4

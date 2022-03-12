###############################################################################
# Project: apres
# Purpose: Packaging configuration for the apres project
# Author:  Paul M. Breen
# Date:    2018-10-13
###############################################################################

from setuptools import setup

setup(name='apres',
      version='0.1',
      description='Package for working with BAS ApRES files',
      url='https://gitlab.data.bas.ac.uk/pbree/apres',
      author='Paul Breen',
      author_email='pbree@bas.ac.uk',
      license='Apache 2.0',
      packages=['apres'],
      scripts=[
          'apres_to_nc.py',
          'nc_to_apres.py',
          'plot_apres.py',
          'read_apres.py',
          'write_apres.py',
      ],
      install_requires=[
          'numpy',
          'netCDF4'
      ])

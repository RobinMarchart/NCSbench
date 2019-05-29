#! /usr/bin/env python3
from setuptools import setup, find_packages
setup(name="ncsbench.common", version="1",
      packages=find_packages(),
      entry_points={'console_scripts': ["ncsbench=common.init:main"]})

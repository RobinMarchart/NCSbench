#! /usr/bin/env python3
from setuptools import setup, find_namespace_packages
setup(name="ncsbench.common", version="1",
      packages=find_namespace_packages(),
      entry_points={'console_scripts': ["ncsbench=ncsbench.common.init:main"]})

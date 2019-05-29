#! /usr/bin/env python3
from setuptools import setup, find_packages
setup(name="ncsbench.robot", version="1",
      packages=find_packages(include=["ncsbench.robot"]),
      install_requires=["ncsbench.common ==1"])

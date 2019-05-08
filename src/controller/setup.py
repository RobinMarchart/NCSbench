#! /usr/bin/env python3
from setuptools import setup, find_namespace_packages
setup(name="ncsbench.controller", version="1",
      packages=find_namespace_packages(include=["ncsbench.controller"]),
      install_requires=["ncsbench.common ==1", "numpy==1.15.4", "scipy==1.1.0"])

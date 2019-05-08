#! /usr/bin/env python3
from setuptools import setup, find_namespace_packages
setup(name="ncsbench.crane", packages=find_namespace_packages(),
      version="1", install_requires=["ncsbench.common ==1"])

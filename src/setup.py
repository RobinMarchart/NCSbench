#! /usr/bin/env python3
from setuptools import setup, find_packages
setup(name="ncsbench", version="1",
      packages=find_packages(),
      entry_points={'console_scripts': ["ncsbench=ncsbench:main"]},install_requires=["numpy==1.15.4", "scipy==1.1.0", "python-ev3dev==1.2.0"],
      include_package_data=True)

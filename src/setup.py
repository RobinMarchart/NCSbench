#! /usr/bin/env python3

from pathlib import Path
from sys import argv
from subprocess import run
from os import chdir
from shutil import copy

out=(Path(argv[0]).parent/"dist").resolve()

if not out.exists():
    out.mkdir()
for f in out.iterdir():
    f.unlink()

p = Path(argv[0]).parent

setup = set()

for c in p.iterdir():
    if c.is_dir():
        for s in c.glob("setup.py"):
            setup.add(s.resolve())

for s in setup:
    chdir(s.parent)
    arg = argv[:]
    arg[0] = str(s)
    run(arg).check_returncode()
    for r in (s.parent/"dist").iterdir():
        copy(str(r), str(out))

del p, setup

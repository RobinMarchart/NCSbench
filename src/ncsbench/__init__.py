
import argparse
from ncsbench.common import main

p=argparse.ArgumentParser()
p.add_argument("--debug",action="store_true")
arg=p.parse_known_args()[0]
if arg.debug:
    breakpoint()
    main(True)
main()


import argparse
p=argparse.ArgumentParser()
p.add_argument("--debug",action="store_true")
arg=p.parse_known_args()[0]
if arg.debug:
    breakpoint()

from ncsbench.common.init import main
main()

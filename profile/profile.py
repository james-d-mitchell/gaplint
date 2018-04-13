#!/usr/bin/env python2 -O
# pylint: skip-file

import cProfile
import os
import pstats
import sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if path not in sys.path:
    sys.path.insert(1, path)
del path

from gaplint import run_gaplint

cmd = "run_gaplint(files=['/Users/jdm/semigroups/gap/tools/' + x for x in os.listdir('/Users/jdm/semigroups/gap/tools')], silent=True)"
cProfile.run(cmd, 'restats')
p = pstats.Stats('restats')
p.sort_stats('cumulative').print_stats(20)

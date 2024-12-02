"""Helper script to pickle expected output of a collection of test files."""

import pickle
import gzip
from glob import glob

import gaplint
from gaplint import main as run_gaplint

_INPUT_FILES = "./tests/input/*"
_EXPECTED_FILENAME = "./tests/expected.pkl.gz"
if __name__ == "__main__":
    diagnostics = []
    for filename in glob(_INPUT_FILES):
        print(filename)
        try:
            run_gaplint(
                files=[filename],
                ranges=True,
                max_warnings=10**23,
                enable=gaplint.Rule.all_codes,
            )
        except SystemExit:
            pass
        diagnostics.extend(gaplint._DIAGNOSTICS)
    print(len(diagnostics))
    with gzip.open(_EXPECTED_FILENAME, "wb") as out_file:
        pickle.dump(diagnostics, out_file)

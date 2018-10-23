"""Main entry point"""

import os.path
import sys

if sys.argv[0].endswith("__main__.py"):

    # We change sys.argv[0] to make help message more useful
    # use executable without path, unquoted
    # (it's just a hint anyway)
    # (if you have spaces in your executable you get what you deserve!)
    executable = os.path.basename(sys.executable)
    sys.argv[0] = executable + " -m unittest"
    del os

__unittest = True

from unittest.main import main  # noqa

main(module=None)

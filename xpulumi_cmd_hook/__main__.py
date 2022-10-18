#!/usr/bin/env python3
#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""xpulumi_cmd_hook CLI"""

import sys
from xpulumi_cmd_hook.cli import run

# allow running with "python3 -m", or as a standalone script
if __name__ == "__main__":
  sys.exit(run())

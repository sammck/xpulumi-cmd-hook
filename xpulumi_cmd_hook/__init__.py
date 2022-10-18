# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Package xpulumi_cmd_hook intercepts the pulumi commandline and redirects to xpulumi
"""

from .version import __version__
from .cli import run
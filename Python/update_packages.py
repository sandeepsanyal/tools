"""
Script updates all python packages using package manager "pip"
"""

import pkg_resources
from subprocess import call

packages = ["pip"] + [  # list all packages with available latest stable updates
    dist.project_name
    for dist in pkg_resources.working_set
]

call(  # update all packages in shell
    "python3 -m pip install --upgrade " + " ".join(packages),
    shell=True
)

del packages

"""
A rudimentary linter for GAP (https://www.gap-system.org/) code.
"""
from setuptools import find_packages, setup

with open("README.rst", "r", encoding="utf8") as f:
    setup(
        name="gaplint",
        version="1.0.3",
        py_modules=["gaplint"],
        url="https://github.com/james-d-mitchell/gaplint",
        license="GPL3",
        author="James D. Mitchell, Simon Tollman",
        author_email="jdm3@st-andrews.ac.uk, skt4@st-andrews.ac.uk",
        description=(
            "A rudimentary linter for GAP "
            + "(https://www.gap-system.org/) code."
        ),
        long_description=f.read(),
        packages=find_packages(exclude=["tests"]),
        include_package_data=True,
        zip_safe=False,
        platforms="any",
        install_requires=["argparse", "pyyaml"],
        entry_points={
            "console_scripts": [
                "gaplint = gaplint:main",
            ],
        },
        classifiers=[
            # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
            "Development Status :: 4 - Beta",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX",
            "Operating System :: MacOS",
            "Operating System :: Unix",
            "Operating System :: Microsoft :: Windows",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )

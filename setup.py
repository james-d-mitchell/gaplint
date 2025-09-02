"""
A rudimentary linter for GAP (https://www.gap-system.org/) code.
"""

from setuptools import find_packages, setup

with open("README.rst", "r", encoding="utf8") as f:
    setup(
        name="gaplint",
        version="1.6.1",
        python_requires=">3.9.0",
        py_modules=["gaplint"],
        url="https://github.com/james-d-mitchell/gaplint",
        license="GPL3",
        author="Reinis Cirpons, James D. Mitchell, Simon Tollman",
        author_email="rc234@st-andrews.ac.uk, jdm3@st-andrews.ac.uk, skt4@st-andrews.ac.uk",
        description=("A linter for GAP (https://www.gap-system.org/)."),
        long_description="""``gaplint`` automatically checks the format of a
        GAP file according to some conventions, which are somewhat
        configurable. It prints the nature and location of instances of any
        instances of violations of these conventions (see the README.rst for
        more details).
        """,
        packages=find_packages(exclude=["tests"]),
        include_package_data=True,
        zip_safe=False,
        platforms="any",
        install_requires=["argparse", "pyyaml", "rich"],
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
            "Programming Language :: Python :: 3",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )

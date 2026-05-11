# setup.py — only used to build the ancrypt Cython extension.
# The anubis package itself is managed via pyproject.toml.
#
# Usage:
#   pip install Cython
#   python setup.py build_ext --inplace

from Cython.Build import cythonize
from setuptools import Extension, setup

setup(
    name="ancrypt",
    ext_modules=cythonize(
        [Extension("ancrypt", ["ancrypt.py"])],
        compiler_directives={"language_level": "3"},
    ),
)

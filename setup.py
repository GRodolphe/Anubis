from setuptools import setup, Extension
from Cython.Build import cythonize

ext_modules = cythonize([
    Extension("ancrypt", ["ancrypt.py"]),
])

setup(
    name="Ancrypt",
    ext_modules=ext_modules,
)

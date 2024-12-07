from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        ["gomoku/utils.pyx"],
        compiler_directives={"language_level": "3"},
    )
)

import numpy
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "cython_main",
        ["cython_main.pyx"],
        include_dirs=[numpy.get_include()],
    ),
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": 3,  # Use Python 3 syntax (f-strings, etc.)
        },
    ),
)

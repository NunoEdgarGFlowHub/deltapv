from setuptools import setup, find_packages

setup(
    name="deltapv",
    version="0.0.1",
    description="Solar cell simulator with automatic differentiation",
    author=
    "Sean Mann, Eric Richard Fadel, Ekin Dogus Cubuk, Sam Schoenholz, and Giuseppe Romano",
    classifiers=["Programming Language :: Python :: 3.7"],
    long_description=open("README.rst").read(),
    install_requires=[
        "numpy", "jax", "jaxlib", "daclasses","matplotlib", "pandas", "pyyaml", "scipy"
    ],
    license="MIT",
    packages=["deltapv"])

from setuptools import setup  # type: ignore

version = "0.1.0"

with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = [
    "rasterio",
    "xarray",
    "earthengine-api",
    "tqdm",
    "requests",
    "netcdf4",
    "joblib",
]
doc_requirements = ["nbsphinx", "sphinx", "sphinx_rtd_theme"]
test_requirements = ["pytest", "requests_mock"]
dev_requirements = (
    [
        "pre-commit",
        "mypy",
        "black",
        "isort",
        "bumpversion",
        "twine",
    ]
    + doc_requirements
    + test_requirements
)

extras_require = {
    "doc": doc_requirements,
    "dev": dev_requirements,
    "test": test_requirements,
}

setup(
    name="wxee",
    author="Aaron Zuspan",
    author_email="aazuspan@gmail.com",
    url="https://github.com/aazuspan/wxee",
    version=version,
    description="Earth Engine to xarray interface",
    long_description=readme + "\n\n",
    long_description_content_type="text/markdown",
    keywords="wxee,xarray,earth-engine",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering :: GIS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Typing :: Typed",
    ],
    license_files=("LICENSE",),
    license="GPLv3+",
    packages=["wxee"],
    test_suite="test",
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require=extras_require,
    python_requires=">=3.7",
)

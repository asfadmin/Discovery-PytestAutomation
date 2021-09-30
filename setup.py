import setuptools
from automation import __version__


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pytest-automation",
    version=__version__,
    # use_scm_version=True,
    description="pytest plugin for building a test suite, using YAML files to extend pytest parameterize functionality.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["automation"],
    url="https://github.com/asfadmin/Discovery-PytestAutomation",
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["pytest-automation = automation.plugin"]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
    install_requires=[
        'pytest',
        'PyYAML',
        'packaging'
    ]
)
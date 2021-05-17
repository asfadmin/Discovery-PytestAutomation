

from setuptools import setup

with open("README.md", "r") as f:
    long_discription = f.read()

setup(
    name="pytest-automation",
    description="pytest plugin for building a test suite, using YAML files.",
    long_discription=long_discription,
    long_description_content_type="text/markdown",
    packages=["automation"],
    url="https://github.com/asfadmin/Discovery-PytestAutomation",
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["automation = automation.main"]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
    install_requires=[
        'PyYAML'
    ]
)
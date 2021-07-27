import setuptools
import subprocess

# Get the version from git and save it:
package_version = subprocess.run(['git', 'describe', '--tags'], stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

if "." not in package_version:
    package_version = "0.0.0"

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pytest-automation",
    version=package_version,
    description="pytest plugin for building a test suite, using YAML files to extend pytest parameterize functionality.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["pytestautomation"],
    url="https://github.com/asfadmin/Discovery-PytestAutomation",
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["pytestautomation = pytestautomation.plugin"]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
    install_requires=[
        'pytest',
        'PyYAML'
    ]
)
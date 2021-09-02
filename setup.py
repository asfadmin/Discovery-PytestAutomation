import setuptools
import subprocess
from packaging.version import Version, InvalidVersion

# Get the version from git and save it:
package_version = subprocess.run(['git', 'describe', '--tags'], stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

try:
    # This guarantees it to be PEP 440 compliant. (Which sometimes, git creates a non-compliant version)
    package_version = str(Version(package_version))
except InvalidVersion:
    package_version = "0.0.0"


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pytest-automation",
    version=package_version,
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
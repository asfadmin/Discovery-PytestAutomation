from packaging.version import Version, InvalidVersion
from setuptools_scm import get_version

try:
    # This guarantees it to be PEP 440 compliant. (Which sometimes, git creates a non-compliant version)
    __version__ = str(Version(get_version()))
except InvalidVersion:
    __version__ = "0.0.0"

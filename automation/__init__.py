from packaging.version import Version, InvalidVersion
import subprocess

# Get the version from git and save it:
package_version = subprocess.run(['git', 'describe', '--tags'], stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

try:
    # This guarantees it to be PEP 440 compliant. (Which sometimes, git creates a non-compliant version)
    __version__ = str(Version(package_version))
except InvalidVersion:
    __version__ = "0.0.0"


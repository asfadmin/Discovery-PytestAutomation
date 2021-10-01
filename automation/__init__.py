from importlib.metadata import version, PackageNotFoundError

try:
    # Get the version (If developing, can be like 1.0.1.dev23+g28a5b36.d20211001)
    __version__ = version("pytest-automation")
except PackageNotFoundError:
    __version__ = "0.0.0"

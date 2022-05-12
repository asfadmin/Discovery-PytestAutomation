from automation import yamlfile # Import WHOLE file, to include it's namespace for "PYTEST_CONFIG_INFO" var
from automation import helpers

import pathlib

# For type hints only:
from pytest import Session, File
from _pytest.config.argparsing import Parser
from py._path.local import LocalPath
from _pytest.nodes import Collector

# Runs once at the start of everything:
# pylint: disable=fixme
#   TODO: Move this to a hook *after* `pytest_collect_file` runs. Can have the collect_file hook look for pytest-config/pytest-managers,
#   to automatically include the norecursedirs logic when searching for them.
#   - From here (https://github.com/pytest-dev/pytest/issues/3261#issuecomment-369740536), seems like `pytest_runtestloop` would be the
#   best hook to use. PROBLEM is pytest-xdist overrides it too, so need to find a way to run *BOTH* ours/theirs, and not just override.
def pytest_sessionstart(session: Session) -> None:
    # Save where NOT to recurse into when searching
    norecursedirs = session.config.getini('norecursedirs')
    # Figure out where core files are in project
    pytest_config_path = helpers.getSingleFileFromName("pytest-config.yml", rootdir=session.config.rootdir, norecursedirs=norecursedirs)
    pytest_managers_path = helpers.getSingleFileFromName("pytest-managers.py", rootdir=session.config.rootdir, norecursedirs=norecursedirs)
    # Load info from said core files:
    test_types_info = helpers.loadTestTypes(pytest_config_path=pytest_config_path, pytest_managers_path=pytest_managers_path)

    # Save info, to use with each test:
    yamlfile.PYTEST_CONFIG_INFO = test_types_info

# Custom CLI options:
def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup('PytestAutomation')
    group.addoption("--only-run-name", "--on", action="append", default=None,
        help = "Only run tests that contains this param in their name.")
    group.addoption("--dont-run-name", "--dn", action="append", default=None,
        help = "Dont run tests that contains this param in their name.")
    group.addoption("--only-run-file", "--of", action="append", default=None,
        help = "Only run yml files that contain this in their name.")
    group.addoption("--dont-run-file", "--df", action="append", default=None,
        help = "Dont run yml files that contain this in their name.")
    group.addoption("--only-run-type", "--ot", action="append", default=None,
        help = "Only run test types that contain this in their name.")
    group.addoption("--dont-run-type", "--dt", action="append", default=None,
        help = "Dont run test types that contain this in their name.")
    group.addoption("--skip-all", action="store_true",
        help = "Skips ALL the tests. (Added for pipeline use).")

# Based on: https://docs.pytest.org/en/6.2.x/example/nonpython.html
def pytest_collect_file(parent: Collector, path: LocalPath) -> File:
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test_"):
        return yamlfile.YamlFile.from_parent(parent, path=pathlib.Path(path))

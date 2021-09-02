from .helpers import getSingleFileFromName, loadTestTypes
from .yamlfile import YamlFile, savePytestConfigInfo

# For type hints:
from pytest import Session, File
from _pytest.config.argparsing import Parser
from py._path.local import LocalPath
from _pytest.nodes import Collector

# Runs once at the start of everything:
def pytest_sessionstart(session: Session) -> None:
    # Figure out where core files are in project
    pytest_config_path = getSingleFileFromName("pytest-config.yml", rootdir=session.config.rootdir)
    pytest_managers_path = getSingleFileFromName("pytest-managers.py", rootdir=session.config.rootdir)
    # Load info from said core files:
    test_types_info = loadTestTypes(pytest_config_path=pytest_config_path, pytest_managers_path=pytest_managers_path)
    
    # Save info to a global, to use with each test:
    savePytestConfigInfo(test_types_info)


## Custom CLI options: 
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
        return YamlFile.from_parent(parent, fspath=path)

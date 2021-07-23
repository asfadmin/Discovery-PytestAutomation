from . import auto as helpers
import os
import sys
import pytest
import glob
import yaml
import re
import importlib
from  copy import deepcopy
import warnings

PYTEST_CONFIG_INFO = None

#### REWRITTING CURRENT HELPERS ####

def remove_submodule_paths(paths: list) -> list:
    submodule_path = os.path.join(os.getcwd(), ".gitmodules")
    # If there are no submodules, nothing to do
    if not os.path.isfile(submodule_path):
        return paths
    # Append path to valid_paths that don't contain a sub-repo
    valid_paths = []
    f = open(submodule_path, "r")
    submodules = re.findall(r"path = (.*)", f.read())
    for path in paths:
        # If any of the path parts name don't match a submodule repo, add it:
        if len([directory for directory in path.split('/') if directory in submodules]) == 0:
            valid_paths.append(path)
    return valid_paths        

def get_file_from_name(name: str) -> str:
    # From your current dir, find all the files with this name:
    recursive_path = os.path.abspath(os.path.join(os.getcwd(), "**", name))
    possible_paths = glob.glob(recursive_path, recursive=True)
    # If any are in a sub-repo/submodule, ignore it. (They might have their *own* config):
    possible_paths = remove_submodule_paths(possible_paths)
    # Make sure you got only found one config:
    assert len(possible_paths) == 1, "WRONG NUMBER OF CONFIGS: Must have exactly one '{0}' file inside project. Found {1} instead.\nBase path used to find files: {2}.".format(name, len(possible_paths), recursive_path)
    return possible_paths[0]

## Open yml/yaml File:
#    Opens it and returns contents, or None if problems happen
def loadYamlFile(path: str):
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        warnings.warn(UserWarning("YAML ERROR: File not found: '{0}'.".format(path)))
    with open(path, "r") as yaml_file:
        try:
            yaml_dict = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            warnings.warn(UserWarning("YAML ERROR: Couldn't read file: '{0}'. Error '{1}'.".format(path, str(e))))
            return None
    if yaml_dict == None:
        warnings.warn(UserWarning("YAML ERROR: File is empty: '{0}'.".format(path)))
    return yaml_dict

## Given "key: val", returns key, val:
#    Usefull with "title: {test dict}" senarios
#    file to report error if something's not formated
def seperateKeyVal(mydict: dict, file: str):
    num_test_titles = len(list(mydict.keys()))
    assert num_test_titles == 1, "MISFORMATTED TEST: {0} keys found in a test. Only have 1, the title of the test. File: {1}".format(num_test_titles, file)
    # return the individual key/val
    name, json_info = next(iter( mydict.items() ))
    return name, json_info


## Validates both pytest_managers.py and pytest_config.py, then loads their methods
# and stores pointers in a dict, for tests to run from.
def loadConfig():
    ## Find pytest_manager.py and pytest_config.yml
    pytest_managers_path = get_file_from_name("pytest_managers.py")
    pytest_config_path = get_file_from_name("pytest_config.yml")

    ## Load those methods, import what's needed. Save as global (to load in each YamlItem)
    pytest_config_info = loadYamlFile(pytest_config_path)

    assert pytest_config_info is not None, "CONFIG ERROR: Could not load pytest_config.py (Check warnings)."
    assert "test_types" in pytest_config_info, "CONFIG ERROR: Required key 'test_types' not found in 'pytest_config.yml'."
    assert isinstance(pytest_config_info["test_types"], type([])), "CONFIG ERROR: 'test_types' must be a list inside 'pytest_config.yml'. (Currently type '{0}').".format(type(master_config["test_types"]))
    
    # Add the path to PYTHONPATH, so you can import pytest_managers:
    sys.path.append(os.path.dirname(pytest_managers_path))
    try:
        # Actually import pytest_managers now:
        pytest_managers_module = importlib.import_module("pytest_managers")
    except ImportError as e:
        assert False, "IMPORT ERROR: Problem importing '{0}'. Error '{1}'.".format(pytest_managers_path, str(e))
    # Done with the import, cleanup your path:
    sys.path.remove(os.path.dirname(pytest_managers_path))

    # Time to load the tests inside the config:
    for ii, test_config in enumerate(pytest_config_info["test_types"]):
        title, test_info = seperateKeyVal(test_config, "pytest_config.yml")

        # If "required_keys" or "required_files" field contain one item, turn into list of that one item:
        if "required_keys" in test_info and not isinstance(test_info["required_keys"], type([])):
            test_info["required_keys"] = [test_info["required_keys"]]
        if "required_files" in test_info and not isinstance(test_info["required_files"], type([])):
            test_info["required_files"] = [test_info["required_files"]]

        # Make sure test_info has required keys:
        assert "method" in test_info, "CONFIG ERROR: Require key 'method' not found in test '{0}'. (pytest_config.yml)".format(title)

        # Import the method inside the module:
        try:
            # This makes it so you can write test_info["method_pointer"](args) to actually call the method:
            test_info["method_pointer"] = getattr(pytest_managers_module, test_info["method"])
        except AttributeError:
            assert False, "IMPORT ERROR: '{0}' not found in 'pytest_managers.py'.\nTried loading from: {1}.\n".format(test_info["method"], pytest_managers_module.__file__)
        # Just a guarantee this field is declared, to pass into functions:
        if "variables" not in test_info:
            test_info["variables"] = None
        # Save it:
        pytest_config_info["test_types"][ii] = test_info

    # Load the hooks:
    if "test_hooks" not in pytest_config_info:
        pytest_config_info["test_hooks"] = {}
    # If trying to do something before the test suite:
    if "before_suites" in pytest_config_info["test_hooks"]:
        try:
            pytest_config_info["test_hooks"]["before_suites_pointer"] = getattr(pytest_managers_module, pytest_config_info["test_hooks"]["before_suites"])
        except AttributeError:
                assert False, "IMPORT ERROR: '{0}' not found in '{1}'.".format(pytest_config_info["test_hooks"]["before_suites"], pytest_managers_module)
    # If trying to do something after the test suite:
    if "after_suites" in pytest_config_info["test_hooks"]:
        try:
            pytest_config_info["test_hooks"]["after_suites_pointer"] = getattr(pytest_managers_module, pytest_config_info["test_hooks"]["after_suites"])
        except AttributeError:
                assert False, "IMPORT ERROR: '{0}' not found in '{1}'.".format(pytest_config_info["test_hooks"]["after_suites"], pytest_managers_module)    
    return pytest_config_info

####################################

def pytest_sessionstart(session):
    config_info = loadConfig()
    ## If hook is defined in pytest_config, run it here.
    if "before_suites" in config_info["test_hooks"]:
        config_info["test_hooks"]["before_suites_pointer"](session)
    # Save info to a global, to use with each test:
    global PYTEST_CONFIG_INFO
    PYTEST_CONFIG_INFO = config_info

def pytest_sessionfinish(session, exitstatus):
    if "aftersuites" in PYTEST_CONFIG_INFO["test_hooks"]:
        # Try first with passing the exitstatus, then w/out:
        #      (Makes exitstatus an optional param)
        try:
            PYTEST_CONFIG_INFO["test_hooks"]["after_suites"](session, exitstatus)
        except TypeError:
            PYTEST_CONFIG_INFO["test_hooks"]["after_suites"](session)

# Based on: https://docs.pytest.org/en/6.2.x/example/nonpython.html
def pytest_collect_file(parent, path):
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test_"):
        return YamlFile.from_parent(parent, fspath=path, test="asdf")

class YamlFile(pytest.File):
    def __init__(self, parent, fspath, test):
        super().__init__(parent=parent, fspath=fspath)
        self.test = test

    def collect(self):
        data = yaml.safe_load(self.fspath.open())

        # Make sure you can load it, and it has tests:
        if data is None or "tests" not in data:
            warnings.warn(UserWarning("Unable to load tests from file: '{0}'.".format(self.fspath)))
            return

        for json_test in data["tests"]:
            name, json_info = seperateKeyVal(json_test, self.fspath)
            yield YamlItem.from_parent(self, name=name, test_info=json_info)
@pytest.fixture
def testingasdf():
    return "SUCCESS"

class YamlItem(pytest.Item):
    def __init__(self, name, parent, test_info):
        super().__init__(name, parent)
        self.name = name
        self.test_info = test_info
    
    def runtest(self):
        pass





# # project root = One dir back from the dir this file is in
# project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# main_config = helpers.getConfig()
# all_tests = helpers.loadTestsFromDirectory(project_root, recurse=True)

# # For each item in the list, run it though the suite:
# @pytest.mark.parametrize("test", all_tests)
# def test_main(test, cli_args):
#     test_info = test[0] # That test's info
#     file_conf = test[1] # Any extra info in that test's yml
#     # Basic error reporting, for when a test fails:
#     error_msg = "\nTitle: '{0}'".format(test_info["title"]) + "\nFile: '{0}'\n".format(file_conf["yml name"])

#     # Skip the test if needed:
#     helpers.skipTestsIfNecessary(test_info["title"], file_conf["yml name"], cli_args)

#     # pass the values to the right function:
#     found_test = False
#     for conf in main_config["test_types"]:
        
#         ## BEGIN normal test_type parsing:

#         # If you declare it, make sure the keys are within that test.
#         if "required_keys" not in conf or set(conf["required_keys"]).issubset(test_info):
#             passed_key_check = True
#         else:
#             passed_key_check = False

#         # If all the tests in a file, belong to a test type:
#         if "required_files" not in conf or file_conf["yml name"] in conf["required_files"]:
#             passed_file_check = True
#         else:
#             passed_file_check = False

#         # Run the test, if all the checks agree:
#         # (I broke this out seperatly, to add more later easily, and to allow you to use more than one at once)
#         if passed_key_check and passed_file_check:
#             found_test = True
#             ## Check if the tester want's to run/exclude a specific *type* of test:
#             # (Can't do this any sooner, needs to make sure the for-loop is on your test-type)
#             if cli_args["only run type"] != None:
#                 title_hit_in_list = False
#                 for only_run_each in cli_args["only run type"]:
#                     if only_run_each.lower() in conf["title"].lower():
#                         title_hit_in_list = True
#                         break
#                 if not title_hit_in_list:
#                     pytest.skip("Type of test did not contain --only-run-type param (case insensitive)")
#             # Same, but reversed for 'dont run':
#             if cli_args["dont run type"] != None:
#                 for dont_run_each in cli_args["dont run type"]:
#                     if dont_run_each.lower() in conf["title"].lower():
#                         pytest.skip("Type of test contained --dont-run-type param (case insensitive)")
            
#             ## Run the test:
#             conf["method_pointer"](test_info, deepcopy(file_conf), deepcopy(cli_args), deepcopy(conf["variables"]))
#             break
#     assert found_test, "Could not find what test this block belongs to. {0}".format(error_msg)

## Custom CLI options: 
def pytest_addoption(parser):
    group = parser.getgroup('PytestAuto')
    group.addoption("--api", action="store", default=None,
        help = "Override which api ALL .yml tests use with this. (DEV/TEST/PROD, or url).")
    group.addoption("--only-run-name", "--on", action="append", default=None,
        help = "Only run tests that contains this param in their name.")
    group.addoption("--dont-run-name", "--dn", action="append", default=None,
        help = "Dont run tests that contains this param in their name.")
    group.addoption("--only-run-file", "--of", action="append", default=None,
        help = "Only run files that contain this in their name.")
    group.addoption("--dont-run-file", "--df", action="append", default=None,
        help = "Dont run files that contain this in their name.")
    group.addoption("--only-run-type", "--ot", action="append", default=None,
        help = "Only run files that contain this in their name.")
    group.addoption("--dont-run-type", "--dt", action="append", default=None,
        help = "Dont run files that contain this in their name.")
    group.addoption("--skip-all", action="store_true",
        help = "Skips ALL the tests. (Added for pipeline use).")


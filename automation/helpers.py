import os           # path, getcwd
import sys          # path
import yaml         # safe_load, YAMLError
import re           # findall
import glob         # glob
import importlib    # import_module
import pytest       # skip
import warnings     # warn

# For type hints:
from typing import Union
from types import ModuleType
from _pytest.config import Config

def removeSubmodulePaths(paths: list, rootdir: str) -> list:
    submodule_path = os.path.join(rootdir, ".gitmodules")
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

def getSingleFileFromName(name: str, rootdir: str) -> str:
    # From your current dir, find all the files with this name:
    recursive_path = os.path.abspath(os.path.join(rootdir, "**", name))
    possible_paths = glob.glob(recursive_path, recursive=True)
    # If any are in a sub-repo/submodule, ignore it. (They might have their *own* config):
    possible_paths = removeSubmodulePaths(possible_paths, rootdir)
    # Make sure you got only found one config:
    assert len(possible_paths) == 1, f"WRONG NUMBER OF FILES: Must have exactly one '{name}' file inside project. Found {len(possible_paths)} instead.\nBase path used to find files: {recursive_path}."
    return possible_paths[0]

## Open yml/yaml File:
#    Opens it and returns contents, or None if problems happen
#    (Or throw if problems happen, if required == True)
def loadYamlFile(path: str, required: bool=False) -> Union[list,dict,None]:
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        error_msg = f"YAML ERROR: File not found: '{path}'."
        # Throw if this is required to work, or warn otherwise
        assert not required, error_msg
        warnings.warn(UserWarning(error_msg))
        return None
    with open(path, "r") as yaml_file:
        try:
            yaml_dict = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            error_msg = f"YAML ERROR: Couldn't read file: '{path}'. Error '{e}'."
            # Throw if this is required to work, or warn otherwise
            assert not required, error_msg
            warnings.warn(UserWarning(error_msg))
            return None
    if yaml_dict is None:
        error_msg = f"YAML ERROR: File is empty: '{path}'."
        # Throw if this is required to work, or warn otherwise
        assert not required, error_msg
        warnings.warn(UserWarning(error_msg))
    return yaml_dict

## Given "key: val", returns key, val:
#    Usefull with "title: {test dict}" senarios
#    file to report error if something's not formated
def seperateKeyVal(mydict: dict, file: str) -> dict:
    num_test_titles = len(list(mydict.keys()))
    assert num_test_titles == 1, f"MISFORMATTED TEST: {num_test_titles} keys found in a test. Only have 1, the title of the test. File: '{file}'."
    # return the individual key/val
    title, test_info = next(iter( mydict.items() ))
    # Make sure the title key isn't in use already, it's reserved:
    assert "title" not in test_info, f"MISFORMATTED TEST: 'title' key found in test '{title}'. This key is reserved for internal use only. File: '{file}'."
    # Save title to test_info. (Might seem reduntant, but this gets all test_info keys at base level, AND still saves the test title)
    test_info["title"] = title
    return test_info

def getPytestManagerModule(pytest_managers_path: str) -> ModuleType:
    # Add the path to PYTHONPATH, so you can import pytest-managers:
    sys.path.append(os.path.dirname(pytest_managers_path))
    try:
        # Actually import pytest-managers now:
        pytest_managers_module = importlib.import_module("pytest-managers")
    except ImportError as e:
        assert False, f"IMPORT ERROR: Problem importing '{pytest_managers_path}'. Error '{e}'."
    # Done with the import, cleanup your path:
    sys.path.remove(os.path.dirname(pytest_managers_path))
    return pytest_managers_module

def skipTestsIfNecessary(config: Config, test_name: str, file_name: str, test_type: str) -> None:
    # If they want to skip EVERYTHING:
    if config.getoption("--skip-all"):
        pytest.skip("Skipping ALL tests. (--skip-all cli arg was found).")
    
    ### ONLY/DONT RUN NAME:
    # If they only want to run something, based on the test title:
    if config.getoption("--only-run-name") is not None:
        # If you match with ANY of the values passed to "--only-run-name":
        found_in_title = False
        for only_run_filter in config.getoption("--only-run-name"):
            if only_run_filter.lower() in test_name.lower():
                # Found it!
                found_in_title = True
                break
        # Check if you found it. If you didn't, skip the test:
        if not found_in_title:
            pytest.skip("Title of test did not contain --only-run-name param (case insensitive)")
    # If they DONT want to run something, based on test title:
    if config.getoption("--dont-run-name") is not None:
        # Nice thing here is, you can skip the second you find it:
        for dont_run_filter in config.getoption("--dont-run-name"):
            if dont_run_filter.lower() in test_name.lower():
                pytest.skip("Title of test contained --dont-run-name param (case insensitive)")
    
    ### ONLY/DONT RUN FILE:
    # If they only want to run something, based on the file name:
    if config.getoption("--only-run-file") is not None:
        # If you match with ANY of the values passed to "--only-run-file":
        found_in_file = False
        for only_run_filter in config.getoption("--only-run-file"):
            if only_run_filter.lower() in file_name.lower():
                # Found it!
                found_in_file = True
                break
        # Check if you found it. If you didn't, skip the test:
        if not found_in_file:
            pytest.skip("Name of file did not contain --only-run-file param (case insensitive)")
    # If they DONT want to run something, based on file name:
    if config.getoption("--dont-run-file") is not None:
        # Nice thing here is, you can skip the second you find it:
        for dont_run_filter in config.getoption("--dont-run-file"):
            if dont_run_filter.lower() in file_name.lower():
                pytest.skip("Name of file contained --dont-run-file param (case insensitive)")

    ### ONLY/DONT RUN TYPE:
    # If they only want to run something, based on the test type:
    if config.getoption("--only-run-type") is not None:
        # If you match with ANY of the values passed to "--only-run-type":
        found_in_type = False
        for only_run_filter in config.getoption("--only-run-type"):
            if only_run_filter.lower() in test_type.lower():
                # Found it!
                found_in_type = True
                break
        # Check if you found it. If you didn't, skip the test:
        if not found_in_type:
            pytest.skip("Test type did not did not contain --only-run-type param (case insensitive)")
    # If they DONT want to run something, based on test type:
    if config.getoption("--dont-run-type") is not None:
        # Nice thing here is, you can skip the second you find it:
        for dont_run_filter in config.getoption("--dont-run-type"):
            if dont_run_filter.lower() in test_type.lower():
                pytest.skip("Test type contained --dont-run-file param (case insensitive)")


## Validates both pytest-managers.py and pytest-config.py, then loads their methods
# and stores pointers in a dict, for tests to run from.
def loadTestTypes(pytest_managers_path: str, pytest_config_path: str) -> dict:
    ## Load those methods, import what's needed. Save as global (to load in each YamlItem)
    pytest_config_info = loadYamlFile(pytest_config_path, required=True)

    assert "test_types" in pytest_config_info, "CONFIG ERROR: Required key 'test_types' not found in 'pytest-config.yml'."
    assert isinstance(pytest_config_info["test_types"], type([])), f"CONFIG ERROR: 'test_types' must be a list inside 'pytest-config.yml'. (Currently type: {type(pytest_config_info['test_types'])})."

    list_of_tests = pytest_config_info["test_types"]

    pytest_managers_module = getPytestManagerModule(pytest_managers_path)

    # Time to load the tests inside the config:
    for ii, test_config in enumerate(list_of_tests):
        test_info = seperateKeyVal(test_config, "pytest-config.yml")

        # If "required_keys" or "required_files" field contain one item, turn into list of that one item:
        if "required_keys" in test_info and not isinstance(test_info["required_keys"], type([])):
            test_info["required_keys"] = [test_info["required_keys"]]
        if "required_files" in test_info and not isinstance(test_info["required_files"], type([])):
            test_info["required_files"] = [test_info["required_files"]]
        # If neither are used, AND you have tests after this one, warn that those tests can't be reached:
        if "required_keys" not in test_info and "required_files" not in test_info and ii < (len(list_of_tests)-1):
            warnings.warn(UserWarning(f"Test type found without required_keys AND required_files used, but there are test types after this one. Tests can't pass '{test_info['title']}' and run on those."))

        # Make sure test_info has required keys:
        assert "method" in test_info, f"CONFIG ERROR: Required key 'method' not found in test '{test_info['title']}'. (pytest-config.yml)"

        # Import the method inside the module:
        try:
            # This makes it so you can write test_info["method_pointer"](args) to actually call the method:
            test_info["method_pointer"] = getattr(pytest_managers_module, test_info["method"])
        except AttributeError:
            assert False, f"IMPORT ERROR: '{test_info['method']}' not found in 'pytest-managers.py'. Tried loading from: '{pytest_managers_module.__file__}'."
        # Just a guarantee this field is declared, to pass into functions:
        if "variables" not in test_info:
            test_info["variables"] = None
        # Save it:
        list_of_tests[ii] = test_info
    return pytest_config_info
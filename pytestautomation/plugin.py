import os
import sys
import pytest
import glob
import yaml
import re
import importlib
import warnings

PYTEST_CONFIG_INFO = {}

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
#    (Or throw if problems happen, if required == True)
def loadYamlFile(path: str, required: bool=False):
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        error_msg = "YAML ERROR: File not found: '{0}'.".format(path)
        # Throw if this is required to work, or warn otherwise
        assert not required, error_msg
        warnings.warn(UserWarning(error_msg))
        return None
    with open(path, "r") as yaml_file:
        try:
            yaml_dict = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            error_msg = "YAML ERROR: Couldn't read file: '{0}'. Error '{1}'.".format(path, str(e))
            # Throw if this is required to work, or warn otherwise
            assert not required, error_msg
            warnings.warn(UserWarning(error_msg))
            return None
    if yaml_dict == None:
        error_msg = "YAML ERROR: File is empty: '{0}'.".format(path)
        # Throw if this is required to work, or warn otherwise
        assert not required, error_msg
        warnings.warn(UserWarning(error_msg))
    return yaml_dict

## Given "key: val", returns key, val:
#    Usefull with "title: {test dict}" senarios
#    file to report error if something's not formated
def seperateKeyVal(mydict: dict, file: str):
    num_test_titles = len(list(mydict.keys()))
    assert num_test_titles == 1, "MISFORMATTED TEST: {0} keys found in a test. Only have 1, the title of the test. File: {1}".format(num_test_titles, file)
    # return the individual key/val
    title, test_info = next(iter( mydict.items() ))
    # Save title to test_info. (Might seem reduntant, but this gets all test_info keys at base level, AND still saves the test title)
    test_info["title"] = title
    return test_info

def getPytestManagerModule(pytest_managers_path: str):
    # Add the path to PYTHONPATH, so you can import pytest_managers:
    sys.path.append(os.path.dirname(pytest_managers_path))
    try:
        # Actually import pytest_managers now:
        pytest_managers_module = importlib.import_module("pytest_managers")
    except ImportError as e:
        assert False, "IMPORT ERROR: Problem importing '{0}'. Error '{1}'.".format(pytest_managers_path, str(e))
    # Done with the import, cleanup your path:
    sys.path.remove(os.path.dirname(pytest_managers_path))
    return pytest_managers_module

def skipTestsIfNecessary(cli_config, test_name, file_name, test_type):
    ## TODO: Look into factoring this to a single method, called three times \/
    # If they want to skip EVERYTHING:
    if cli_config.getoption("--skip-all"):
        pytest.skip("Skipping ALL tests. (--skip-all cli arg was found).")
    
    ### ONLY/DONT RUN NAME:
    # If they only want to run something, based on the test title:
    if cli_config.getoption("--only-run-name") != None:
        # If you match with ANY of the values passed to "--only-run-name":
        found_in_title = False
        for only_run_filter in cli_config.getoption("--only-run-name"):
            if only_run_filter.lower() in test_name.lower():
                # Found it!
                found_in_title = True
                break
        # Check if you found it. If you didn't, skip the test:
        if not found_in_title:
            pytest.skip("Title of test did not contain --only-run-name param (case insensitive)")
    # If they DONT want to run something, based on test title:
    if cli_config.getoption("--dont-run-name") != None:
        # Nice thing here is, you can skip the second you find it:
        for dont_run_filter in cli_config.getoption("--dont-run-name"):
            if dont_run_filter.lower() in test_name.lower():
                pytest.skip("Title of test contained --dont-run-name param (case insensitive)")
    
    ### ONLY/DONT RUN FILE:
    # If they only want to run something, based on the file name:
    if cli_config.getoption("--only-run-file") != None:
        # If you match with ANY of the values passed to "--only-run-file":
        found_in_file = False
        for only_run_filter in cli_config.getoption("--only-run-file"):
            if only_run_filter.lower() in file_name.lower():
                # Found it!
                found_in_file = True
                break
        # Check if you found it. If you didn't, skip the test:
        if not found_in_file:
            pytest.skip("Name of file did not contain --only-run-file param (case insensitive)")
    # If they DONT want to run something, based on file name:
    if cli_config.getoption("--dont-run-file") != None:
        # Nice thing here is, you can skip the second you find it:
        for dont_run_filter in cli_config.getoption("--dont-run-file"):
            if dont_run_filter.lower() in file_name.lower():
                pytest.skip("Name of file contained --dont-run-file param (case insensitive)")

    ### ONLY/DONT RUN TYPE:
    # If they only want to run something, based on the test type:
    if cli_config.getoption("--only-run-type") != None:
        # If you match with ANY of the values passed to "--only-run-type":
        found_in_type = False
        for only_run_filter in cli_config.getoption("--only-run-type"):
            if only_run_filter.lower() in test_type.lower():
                # Found it!
                found_in_type = True
                break
        # Check if you found it. If you didn't, skip the test:
        if not found_in_type:
            pytest.skip("Test type did not did not contain --only-run-type param (case insensitive)")
    # If they DONT want to run something, based on test type:
    if cli_config.getoption("--dont-run-type") != None:
        # Nice thing here is, you can skip the second you find it:
        for dont_run_filter in cli_config.getoption("--dont-run-type"):
            if dont_run_filter.lower() in test_type.lower():
                pytest.skip("Test type contained --dont-run-file param (case insensitive)")


## Validates both pytest_managers.py and pytest_config.py, then loads their methods
# and stores pointers in a dict, for tests to run from.
def loadTestTypes(pytest_managers_path: str, pytest_config_path: str):
    ## Load those methods, import what's needed. Save as global (to load in each YamlItem)
    pytest_config_info = loadYamlFile(pytest_config_path, required=True)

    assert "test_types" in pytest_config_info, "CONFIG ERROR: Required key 'test_types' not found in 'pytest_config.yml'."
    assert isinstance(pytest_config_info["test_types"], type([])), "CONFIG ERROR: 'test_types' must be a list inside 'pytest_config.yml'. (Currently type '{0}').".format(type(pytest_config_info["test_types"]))

    list_of_tests = pytest_config_info["test_types"]

    pytest_managers_module = getPytestManagerModule(pytest_managers_path)

    # Time to load the tests inside the config:
    for ii, test_config in enumerate(list_of_tests):
        test_info = seperateKeyVal(test_config, "pytest_config.yml")

        # If "required_keys" or "required_files" field contain one item, turn into list of that one item:
        if "required_keys" in test_info and not isinstance(test_info["required_keys"], type([])):
            test_info["required_keys"] = [test_info["required_keys"]]
        if "required_files" in test_info and not isinstance(test_info["required_files"], type([])):
            test_info["required_files"] = [test_info["required_files"]]

        # Make sure test_info has required keys:
        assert "method" in test_info, "CONFIG ERROR: Require key 'method' not found in test '{0}'. (pytest_config.yml)".format(test_info["title"])

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
        list_of_tests[ii] = test_info
    return { "test_types": list_of_tests }


def loadTestHooks(pytest_managers_path: str, pytest_config_path: str):
    pytest_config_info = loadYamlFile(pytest_config_path, required=True)
    pytest_managers_module = getPytestManagerModule(pytest_managers_path)

    # Load the hooks, if they exist:
    if "test_hooks" not in pytest_config_info:
        return { "test_hooks": {} }

    # Make sure it's formated correctly:
    test_hooks_info = pytest_config_info["test_hooks"]
    assert isinstance(test_hooks_info, type({})), "CONFIG ERROR: Inside 'pytest_config.yml', 'test_hooks' must contain a DICT of wanted hooks. (Currently type '{0}'.)".format(type(test_hooks_info))

    ### HOOKS FOR TEST SUITE:
    # If trying to do something before the test suite:
    if "before_suites" in test_hooks_info:
        try:
            test_hooks_info["before_suites_pointer"] = getattr(pytest_managers_module, test_hooks_info["before_suites"])
        except AttributeError:
                assert False, "IMPORT ERROR: '{0}' not found in '{1}'.".format(test_hooks_info["before_suites"], pytest_managers_module)
    # If trying to do something after the test suite:
    if "after_suites" in test_hooks_info:
        try:
            test_hooks_info["after_suites_pointer"] = getattr(pytest_managers_module, test_hooks_info["after_suites"])
        except AttributeError:
                assert False, "IMPORT ERROR: '{0}' not found in '{1}'.".format(test_hooks_info["after_suites"], pytest_managers_module)    
    return { "test_hooks": test_hooks_info }

def loadAddCliOptions(pytest_managers_path: str, pytest_config_path: str):
    pytest_config_info = loadYamlFile(pytest_config_path, required=True)
    pytest_managers_module = getPytestManagerModule(pytest_managers_path)

    # Start parsing the extra options, if they exist:
    if "add_cli_options" not in pytest_config_info:
        return { "add_cli_options": {} }

    # Make sure it's formated correctly:
    add_cli_options_info = pytest_config_info["add_cli_options"]
    assert isinstance(add_cli_options_info, type([])), "CONFIG ERROR: Inside 'pytest_config.yml', 'add_cli_options' must contain a LIST of wanted hooks. (Currently type '{0}'.)".format(type(add_cli_options_info))

    #############################
    # TODO: PLACEHOLDER While I finish this section
    # Note, maybe this is not needed? Look what happens if searchAPI has
    # It's own conftest.py that adds options. Maybe it'll pull it correctly still
    return { "add_cli_options": {} }
    #############################

    # NOTE for checking if type == str, or custom function:
    # Use https://stackoverflow.com/questions/38171243/python-check-for-class-existance
    try:
        var = file_type() # This won't throw if it's "str" or something
    except NameError:
        # Now try to load it from pytest_managers.py
        pass

####################################

# Runs once at the start of everything:
def pytest_sessionstart(session):
    # Figure out where core files are in project
    pytest_config_path = get_file_from_name("pytest_config.yml")
    pytest_managers_path = get_file_from_name("pytest_managers.py")

    # Load info from said core files:
    # (Format of returned dicts is still {"main_key": {ALL_KEY_VALS_HERE}}, so different
    #   "load*" methods don't conflict with one anther. i.e. test_hooks == {"test_hooks": {ALL_ACTUALL_INFO_HERE}})
    test_types_info = loadTestTypes(pytest_config_path=pytest_config_path, pytest_managers_path=pytest_managers_path)
    test_hooks_info = loadTestHooks(pytest_config_path=pytest_config_path, pytest_managers_path=pytest_managers_path)
    
    # Save info to a global, to use with each test:
    global PYTEST_CONFIG_INFO
    PYTEST_CONFIG_INFO.update(test_types_info)
    PYTEST_CONFIG_INFO.update(test_hooks_info)

    ## If hook is defined in pytest_config.yml, run it here.
    if "before_suites" in PYTEST_CONFIG_INFO["test_hooks"]:
        PYTEST_CONFIG_INFO["test_hooks"]["before_suites_pointer"](session)


# Runs once when the entire suite finishes:
def pytest_sessionfinish(session, exitstatus):
    if "after_suites" in PYTEST_CONFIG_INFO["test_hooks"]:
        # Try first with passing the exitstatus, then w/out:
        #      (Makes exitstatus an optional param)
        try:
            PYTEST_CONFIG_INFO["test_hooks"]["after_suites"](session, exitstatus)
        except TypeError:
            PYTEST_CONFIG_INFO["test_hooks"]["after_suites"](session)

## Custom CLI options: 
def pytest_addoption(parser):
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

    ## START Looking if any are declared in the config:
    ## (MAYBE not needed, see how conftest works when inside SearchAPI)
    # Figure out where core files are in project
    pytest_config_path = get_file_from_name("pytest_config.yml")
    pytest_managers_path = get_file_from_name("pytest_managers.py")
    add_cli_options_info = loadAddCliOptions(pytest_config_path=pytest_config_path, pytest_managers_path=pytest_managers_path)

    # if "add_cli_options" in PYTEST_CONFIG_INFO:
    #     print("HITTTTT")
    # group.addoption("--api", action="store", default=None,
    #     help = "Override which api ALL .yml tests use with this. (DEV/TEST/PROD, or url).")



# Based on: https://docs.pytest.org/en/6.2.x/example/nonpython.html
def pytest_collect_file(parent, path):
    if path.ext in [".yml", ".yaml"] and path.basename.startswith("test_"):
        return YamlFile.from_parent(parent, fspath=path)

class YamlFile(pytest.File):
    ## Default init used. Declared: self.parent, self.fspath

    def get_name(self):
        return os.path.basename(self.fspath)

    def collect(self):
        data = yaml.safe_load(self.fspath.open())

        # Make sure you can load it, and it has tests:
        if data is None or "tests" not in data:
            warnings.warn(UserWarning("Unable to load tests from file: '{0}'.".format(self.fspath)))
            return

        for json_test in data["tests"]:
            test_info = seperateKeyVal(json_test, self.fspath)
            yield YamlItem.from_parent(self, test_info=test_info)

class YamlItem(pytest.Item):

    def __init__(self, parent, test_info):
        super().__init__(test_info["title"], parent)
        self.file_name = parent.get_name()
        self.test_info = test_info

    def runtest(self):
        # Look for the right config to run off of:
        found_test = False
        for poss_test_type in PYTEST_CONFIG_INFO["test_types"]:
            # *IF* required_keys are declared, make sure the test only runs if THOSE keys are inside the test info:
            passed_key_check = True if "required_keys" not in poss_test_type or set(poss_test_type["required_keys"]).issubset(self.test_info) else False
            # *IF* required_files are declared, make sure only those files are ran:
            passed_file_check = True if "required_files" not in poss_test_type or self.file_name in poss_test_type["required_files"] else False

            # If you pass both filters, congrats! You can run the test:
            if passed_key_check and passed_file_check:
                found_test = True
                skipTestsIfNecessary(cli_config=self.config, test_name=self.test_info["title"], file_name=self.file_name, test_type=poss_test_type["title"])

                # poss_test_type["method_pointer"](self.test_info, self.config, poss_test_type["variables"])
                # Need to pass in: config, test_info, test_type_vars
                # Old args passed in: test_info, file_conf, cli_args, test_type_vars
                # (Put "file_info" inside test_info? Maybe under it's own "file_info" key?)

                # You're done. Don't check ALL test types, only the FIRST match
                break
        assert found_test, "TEST TYPE NOT FOUND: Could not find which manager to use with this test."

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        # if isinstance(excinfo.value, yaml.YamlException):
        return "\n".join(
            [
                "Test failed",
                "   Message: {0}: {1}".format(excinfo.type.__name__, excinfo.value),
                "   Test: '{0}'".format(self.test_info["title"]),
                "   File: '{0}'".format(self.file_name),
                "   Traceback: {0}".format(excinfo.traceback[-1:][0])
            ]
        )

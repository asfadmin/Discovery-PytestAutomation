import pytest               # To use asserts and fixtures
import glob, re             # To recursivly find all ymls
import yaml                 # To open the ymls
import os, sys              # For path manipulation/joining
import importlib            # For returning modules back to the main script
from copy import deepcopy   # To copy dicts w/out modifying original

# GLOBALS:
import_file_name = "pytest_managers.py"
config_file_name = "pytest_config.yml"
loaded_config = None # Gets set to contents of config_path, in 'import_config'

def get_project_root():
    # Recurse back until you hit a .git folder:
    git_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".git"))
    while not os.path.exists(git_root):
        git_root = os.path.abspath(os.path.join(os.path.dirname(git_root), "..", ".git"))
        assert git_root != "/.git", "PytestAutomation is not inside a repo. Could not find a .git folder behind this one."
    # Take off the .git and return the path.
    return os.path.dirname(git_root)

def remove_submodules_from_paths(list_of_paths):
    global project_root
    submodule_path = os.path.join(project_root, ".gitmodules")
    # If there are no submodules, nothing to do
    if not os.path.isfile(submodule_path):
        return list_of_paths
    # Append path to valid_paths that don't contain a sub-repo
    valid_paths = []
    f = open(submodule_path, "r")
    submodules = re.findall(r"path = (.*)", f.read())
    for path in list_of_paths:
        # If any of the path pieces are a submodule repo:
        if len([directory for directory in path.split('/') if directory in submodules]) == 0:
            valid_paths.append(path)
    return valid_paths

# Looks through project, starting at project_root, and does NOT go into submodules:
#   (Returns the path if exactly 1 file is found, or throws an error)
def get_path_from_name(name):
    global project_root
    recursive_path = os.path.abspath(os.path.join(project_root, "**", name))
    possible_paths = glob.glob(recursive_path, recursive=True)
    # Exclude all submodules this repo is in. (Stops it from conflicting with itself if those submodules contains this test framework)
    possible_paths = remove_submodules_from_paths(possible_paths)

    if len(possible_paths) != 1:
        assert False, "Must have exactly one file named {0} inside project. Found {1} instead.\nPath used to find files: {2}.".format(name, len(possible_paths), recursive_path)
    return possible_paths[0]

project_root = get_project_root()
import_path = get_path_from_name(import_file_name)
config_path = get_path_from_name(config_file_name)

####################
# HELPER FUNCTIONS #
####################
## Open yml (and yaml) File:
# Gets called for each yml/yaml file. 
#    Opens it and returns a list of tests, or None if none are found.
#    format: {"tests": [list,of,tests,here] }
def openYmlFile(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print("\n###########")
        print("File not Found: '{0}'.".format(path))
        print("###########\n")
        return None
    with open(path, "r") as yaml_file:
        try:
            yaml_dict = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            print("\n###########")
            print("Failed to parse yaml: '{0}'.".format(path))
            print("###########\n")
            return None
    if yaml_dict == None:
        print("\n###########")
        print("Yaml file is empty: '{0}'.".format(path))
        print("###########\n")
    return yaml_dict

## Move title into Test:
# change from {"title_a" : {data1: 1,data2: 2}} to {title: "title_a", data1: 1, data2: 2},
#       or 'None' if impossible
def moveTitleIntoBlock(json_test, file_name):
    keys = list(json_test.keys())
    if len(keys) != 1:
        print("\n###########")
        print("Yaml not formatted correctly. File: '{0}'. Test: '{1}'.".format(file_name, str(test)))
        print("###########\n")
        return None
    title = keys[0]
    json_test = next(iter(json_test.values()))
    json_test["title"] = title
    return json_test


##################
# LOAD FUNCTIONS #
##################
# Import the methods defined in config:
def import_config():
    global config_path
    global import_path

    # openymlfile will print details on what goes wrong:
    master_config = openYmlFile(config_path)
    import_name = os.path.basename(import_path)[:-3] # [:-3] to take off the '.py'

    #  Quick sanity checks:
    assert master_config != None, "Problem with yml config. Path: '{0}'.".format(config_path)
    assert "test_types" in master_config, "Required key 'test_types' not found in {0}.".format(import_name)
    assert isinstance(master_config["test_types"], type([])), "Problem in {0}: 'test_types' must be a list. (Currently type: {1}).".format(os.path.basename(import_path), type(master_config["test_types"]))
    # Import the 'import_name' package:
    try:
        # Lets you import files from the 'import' dir:
        sys.path.append(os.path.dirname(import_path))
        import_main = importlib.import_module(import_name)
        sys.path.remove(os.path.dirname(import_path))
    except ImportError as e:
        assert False, "Problem importing file '{0}'. Tried to import: '{1}'.\nError: {2}".format(import_name, import_path, str(e))

    ## LOAD TEST_TYPES BLOCK ##
    # (These are required. No need to check for key-errors)
    # For each test inside config, make sure it's formatted correctly, and load its testing func:
    for i, test_config in enumerate(master_config["test_types"]):
        tmp_config = moveTitleIntoBlock(test_config, "pytest_config.yml")
        # Make sure the config block parsed correctly, and contains the required keys:
        assert tmp_config != None, "Error parsing config. Block: '{0}'.".format(test_config)
        assert "required_keys" in tmp_config and "method" in tmp_config, "Required keys not found. (Keys: required_keys, method). \nBlock: '{0}'.".format(test_config)


        # If required_keys contains only one item, make it a list of one item:
        if not isinstance(tmp_config["required_keys"], type([])):
            tmp_config["required_keys"] = [tmp_config["required_keys"]]
        # Import the method from the module:
        try:
            # Saves the function to the 'method' key.
            # From here, you should be able to call tmp_config["method"](test_info) to run a test
            tmp_config["method_pointer"] = getattr(import_main, tmp_config["method"])
        except AttributeError:
            assert False, "'{0}' not found in '{1}'.\nTried loading from: {2}.\n".format(tmp_config["method"], import_name, import_main.__file__)
        # Just guarantee it's there, for passing onto each test:
        if "variables" not in tmp_config:
            tmp_config["variables"] = None
        # Save it:
        master_config["test_types"][i] = tmp_config

    ## LOAD TEST_HOOKS BLOCK ##
    # (These are NOT required, check for key-errors)
    if "test_hooks" in master_config:
        if "before_suites" in master_config["test_hooks"]:
            try:
                # override the before-hook with it's function:
                master_config["test_hooks"]["before_suites"] = getattr(import_main, master_config["test_hooks"]["before_suites"])
            except AttributeError:
                assert False, "'{0}' not found in '{1}'.".format(master_config["test_hooks"]["before_suites"], import_name)
        if "after_suites" in master_config["test_hooks"]:
            try:
                # override the before-hook with it's function:
                master_config["test_hooks"]["after_suites"] = getattr(import_main, master_config["test_hooks"]["after_suites"])
            except AttributeError:
                assert False, "'{0}' not found in '{1}'.".format(master_config["test_hooks"]["after_suites"], import_name)
    else:
        master_config["test_hooks"] = {}
    return master_config
loaded_config = import_config()

## Imports the functions defined in the config, and returns them w/ everything in a dict. 
def getConfig():
    global loaded_config
    return loaded_config

## Load all yml's in repo, and return a list of formated tests:
def loadTestsFromDirectory(dir_path_root, recurse=False):
    tests_pattern = os.path.join(dir_path_root, "**", "test_*.y*ml")
    list_of_tests = []
    # Get all yml tests, then remove any that are outside of repo being tested:
    list_of_test_paths = glob.glob(tests_pattern, recursive=recurse)
    list_of_test_paths = remove_submodules_from_paths(list_of_test_paths)
    for file in list_of_test_paths:
        yaml_dict = openYmlFile(file)
        if yaml_dict == None:
            print("PROBLEM PARSING YML: '{0}'. Skipping it.".format(file))
            continue
        if not ("tests" in yaml_dict and isinstance(yaml_dict["tests"], type([]))):
            print("\n###########")
            print("No tests found in Yaml: '{0}'. File needs 'tests' key, with a list as the value.".format(file))
            print("###########\n")
            continue

        # file config is everything else in the file,
        #   (incase you want to have an override for all tests. i.e.=> print: False)
        file_config = deepcopy(yaml_dict)
        file_config["yml name"] = os.path.basename(file)
        del file_config["tests"]

        # Add each test/config to the master-list:
        for test in yaml_dict["tests"]:
            test = moveTitleIntoBlock(test, file)
            # Each test maybe inside a different test file with it's unique config:
            list_of_tests.append((test, file_config))
    return list_of_tests


##################
# HOOK FUNCTIONS #
##################
def pytest_sessionstart(session):
    global loaded_config
    # If they declared a before-hook, run it:
    if "before_suites" in loaded_config["test_hooks"]:
        loaded_config["test_hooks"]["before_suites"]()

def pytest_sessionfinish(session, exitstatus):
    global loaded_config
    # If they declared a after-hook:
    if "after_suites" in loaded_config["test_hooks"]:
        # Try first with passing the exitstatus, then w/out:
        #      (Makes exitstatus an optional param)
        try:
            loaded_config["test_hooks"]["after_suites"](exitstatus)
        except TypeError as e:
            loaded_config["test_hooks"]["after_suites"]()

#############
# CLI STUFF #
#############
## Custom CLI options: 
def pytest_addoption(parser):
    parser.addoption("--api", action="store", default=None,
        help = "Override which api ALL .yml tests use with this. (DEV/TEST/PROD, or url).")
    parser.addoption("--only-run", action="append", default=None,
        help = "Only run tests that contains this param in their name.")
    parser.addoption("--dont-run", action="append", default=None,
        help = "Dont run tests that contains this param in their name.")
    parser.addoption("--only-run-file", action="append", default=None,
        help = "Only run files that contain this in their name.")
    parser.addoption("--dont-run-file", action="append", default=None,
        help = "Dont run files that contain this in their name.")

## Returns the custom CLI options to a test when used in a param:
@pytest.fixture
def cli_args(request):
    global loaded_config

    def lookup_api(poss_key):
        if poss_key in loaded_config["api_urls"]:
            # Change poss_key from api_urls key, to value:
            poss_key = loaded_config["api_urls"][poss_key]
        # else: assume the 'poss_key' passed IS the url itself. No need to error out
        if poss_key[-1:] != '/':
            poss_key += '/'
        return poss_key

    all_args = {}
    # Api holds the start of the url. Each test adds their endpoint.
    # If '--api' was used in the commandline:
    if request.config.getoption('--api') != None:
        all_args["api"] = lookup_api(request.config.getoption('--api'))
    # Elif try to load the 'default' api from config:
    elif "api_urls" in loaded_config and "default" in loaded_config["api_urls"]:
        all_args["api"] = lookup_api(loaded_config["api_urls"]["default"])
    # Else you're done:
    else:
        all_args['api'] = None

    all_args['only run'] = request.config.getoption('--only-run')
    all_args['dont run'] = request.config.getoption('--dont-run')
    all_args['only run file'] = request.config.getoption('--only-run-file')
    all_args['dont run file'] = request.config.getoption('--dont-run-file')
    return all_args


##################
# UTIL FUNCTIONS #
##################
def skipTestsIfNecessary(test_name, file_name, cli_args):
    only_run_cli = cli_args['only run']
    dont_run_cli = cli_args['dont run']
    only_run_file_cli = cli_args['only run file']
    dont_run_file_cli = cli_args['dont run file']

    ## If they passed '--only-run val', and val not in test title:
    if only_run_cli != None:
        # Might be in one element of the list, but not the other:
        title_in_cli_list = False
        for only_run_each in only_run_cli:
            if only_run_each.lower() in test_name.lower():
                title_in_cli_list = True
                break
        if not title_in_cli_list:
            pytest.skip("Title of test did not contain --only-run param (case insensitive)")

    ## Same, but reversed for '--dont-run':
    if dont_run_cli != None:
        # Black list, skip as soon as you hit it:
        for dont_run_each in dont_run_cli:
            if dont_run_each.lower() in test_name.lower():
                pytest.skip("Title of test contained --dont-run param (case insensitive)")

    ## Same as above two, but now for the <file> variants:
    if only_run_file_cli != None:
        # Might be in one element of the list, but not the other:
        file_in_cli_list = False
        for only_run_each in only_run_file_cli:
            if only_run_each.lower() in file_name.lower():
                file_in_cli_list = True
                break
        if not file_in_cli_list:
            pytest.skip("File test was in did not match --only-run-file param (case insensitive)")
    if dont_run_file_cli != None:
        # Black list, skip as soon as you hit it:
        for dont_run_each in dont_run_file_cli:
            if dont_run_each.lower() in file_name.lower():
                pytest.skip("File test was in matched --dont-run-file param (case insensitive)")

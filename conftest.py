import pytest               # To use asserts and fixtures
import glob                 # To recursivly find all ymls
import yaml                 # To open the ymls
import os                   # For path manipulation/joining
import importlib            # For returning modules back to the main script
from copy import deepcopy   # To copy dicts w/out modifying original

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
    all_args = {}
    all_args['api'] = request.config.getoption('--api')
    all_args['only run'] = request.config.getoption('--only-run')
    all_args['dont run'] = request.config.getoption('--dont-run')
    all_args['only run file'] = request.config.getoption('--only-run-file')
    all_args['dont run file'] = request.config.getoption('--dont-run-file')
    return all_args


####################
# HELPER FUNCTIONS #
####################
## Open yml (and yaml) File:
# Gets called for each yml/yaml file. 
#    Opens it and returns a list of tests, or None if none are found.
#    format: {"tests": [list,of,tests,here] }
def openYmlFile(path):
    if not os.path.exists(path):
        print("\n###########")
        print("File not Found: {0}.".format(path))
        print("###########\n")
        return None
    with open(path, "r") as yaml_file:
        try:
            yaml_dict = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            print("\n###########")
            print("Failed to parse yaml: {0}.".format(path))
            print("###########\n")
            return None
    return yaml_dict

## Move title into Test:
# change from {"title_a" : {data1: 1,data2: 2}} to {title: "title_a", data1: 1, data2: 2},
#       or 'None' if impossible
def moveTitleIntoBlock(json_test, file_name):
    keys = list(json_test.keys())
    if len(keys) != 1:
        print("\n###########")
        print("Yaml not formatted correctly. File: {0}. Test: {1}.".format(file_name, str(test)))
        print("###########\n")
        return None
    title = keys[0]
    json_test = next(iter(json_test.values()))
    json_test["title"] = title
    return json_test




##################
# LOAD FUNCTIONS #
##################
## Load/verify the config. 
def loadConfigFromDirectory(dir_path, config_name="pytest_config.yml", import_name="pytest_managers"):
    # If they forgot the .py, add it. (Gets removed when importing modules):
    if import_name[-3:] != ".py":
        import_name = import_name + ".py"
    # Save the paths
    master_config_path = os.path.abspath(os.path.join(dir_path, config_name))

    master_config = openYmlFile(master_config_path)
    # openymlfile will print details on what goes wrong too:
    assert master_config != None, "Problem with yml config. Path: {0}.".format(master_config_path)

    # Import the 'import_name' package:
    try:
        full_import = "yml_tests." + import_name[:-3]
        import_main = importlib.import_module("yml_tests." + import_name[:-3])
    except ImportError:
        assert False, "Problem importing file '{0}'. Tried to import: '{1}'.".format(import_name, full_import)

    # For each test inside config, make sure it's formatted correctly, and load its testing func:
    for i, test_config in enumerate(master_config["test_types"]):
        tmp_config = moveTitleIntoBlock(test_config, "pytest_config.yml")
        # Make sure the config block parsed correctly, and contains the required keys:
        assert tmp_config != None, "Error parsing config. Block: {0}.".format(test_config)
        assert "required_keys" in tmp_config and "method" in tmp_config, "Required keys not found. (Keys: required_keys, method). \nBlock: {0}.".format(test_config)
        # If required_keys contains only one item, make it a list of one item:
        if not isinstance(tmp_config["required_keys"], type([])):
            tmp_config["required_keys"] = [tmp_config["required_keys"]]
        # Import the method from the module:
        try:
            # Saves the function to the 'method' key.
            # From here, you should be able to call tmp_config["method"](test_info) to run a test
            tmp_config["method"] = getattr(import_main, tmp_config["method"])
        except AttributeError:
            assert False, "'{0}' not found in {1}.".format(tmp_config["method"], import_name)
        # Save it:
        master_config["test_types"][i] = tmp_config
    return master_config

## Load all yml's in repo, and return a list of formated tests:
def loadTestsFromDirectory(dir_path_root, recurse=False):
    tests_pattern = os.path.join(dir_path_root, "**", "test_*.y*ml")
    list_of_tests = []
    for file in glob.glob(tests_pattern, recursive=recurse):
        yaml_dict = openYmlFile(file)
        if not ("tests" in yaml_dict and isinstance(yaml_dict["tests"], type([]))):
            print("\n###########")
            print("No tests found in Yaml: {0}. File needs 'tests' or 'url tests' key, with a list as the value.".format(file))
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

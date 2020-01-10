import pytest, glob, yaml, os
from copy import deepcopy

## Custom CLI options: 
def pytest_addoption(parser):
    parser.addoption("--api", action="store", default=None,
        help = "Override which api ALL .yml tests use with this. (DEV/PROD or SOME-URL).")
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


## Load all yml's in repo, and return a list of formated tests:
def loadTestsFromDirectory(dir_path_root, recurse=False):
    
    ## Open yml (and yaml) File:
    # Gets called for each yml/yaml file. 
    #    Opens it and returns a list of tests, or None if none are found.
    #    format: {"tests": [list,of,tests,here] }
    def openYmlFile(path):
        if not os.path.exists(path):
            print("\n###########")
            print("File not Found: {0}. Error: {1}".format(path, str(e)))
            print("###########\n")
            return None
        with open(path, "r") as yaml_file:
            try:
                yaml_dict = yaml.safe_load(yaml_file)
            except yaml.YAMLError as e:
                print("\n###########")
                print("Failed to parse yaml: {0}. Error: {1}".format(path, str(e)))
                print("###########\n")
                return None
        return yaml_dict

    ## Move title into Test:
    # change from {"title_a" : {data1: 1,data2: 2}} to {title: "title_a", data1: 1, data2: 2},
    #       or 'None' if impossible
    def moveTitleIntoTest(json_test, file_name):
        keys = list(json_test.keys())
        if len(keys) != 1:
            print("\n###########")
            print("Yaml test not formatted correctly. File: {0}. Test: {1}.".format(file_name, str(test)))
            print("###########\n")
            return None
        title = keys[0]
        json_test = next(iter(json_test.values()))
        json_test["title"] = title
        return json_test

    #######################
    # BEGIN LOADING TESTS #
    #######################
    master_config = openYmlFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "pytest_config.yml"))
    # for test_config, i in enumerate(master_config["test_types"]):
    #     print(test_config)
    #     master_config["test_types"][i] = moveTitleIntoTest(test_config, "pytest_config.yml")
    print(master_config)
    exit()
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
        del file_config["tests"]

        # Add each test/config to the master-list:
        for test in yaml_dict["tests"]:
            test = moveTitleIntoTest(test, file)
            # Each test maybe inside a different test file with it's unique config:
            list_of_tests.append((test, file_config))
    return list_of_tests
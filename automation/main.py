from . import auto as helpers
import os
import pytest
from  copy import deepcopy

# project root = One dir back from the dir this file is in
project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
main_config = helpers.getConfig()
all_tests = helpers.loadTestsFromDirectory(project_root, recurse=True)

# For each item in the list, run it though the suite:
@pytest.mark.parametrize("test", all_tests)
def test_main(test, cli_args):
    test_info = test[0] # That test's info
    file_conf = test[1] # Any extra info in that test's yml
    # Basic error reporting, for when a test fails:
    error_msg = "\nTitle: '{0}'".format(test_info["title"]) + "\nFile: '{0}'\n".format(file_conf["yml name"])

    # Skip the test if needed:
    helpers.skipTestsIfNecessary(test_info["title"], file_conf["yml name"], cli_args)

    # pass the values to the right function:
    found_test = False
    for conf in main_config["test_types"]:
        
        ## BEGIN normal test_type parsing:

        # If you declare it, make sure the keys are within that test.
        if "required_keys" not in conf or set(conf["required_keys"]).issubset(test_info):
            passed_key_check = True
        else:
            passed_key_check = False

        # If all the tests in a file, belong to a test type:
        if "required_files" not in conf or file_conf["yml name"] in conf["required_files"]:
            passed_file_check = True
        else:
            passed_file_check = False

        # Run the test, if all the checks agree:
        # (I broke this out seperatly, to add more later easily, and to allow you to use more than one at once)
        if passed_key_check and passed_file_check:
            found_test = True
            ## Check if the tester want's to run/exclude a specific *type* of test:
            # (Can't do this any sooner, needs to make sure the for-loop is on your test-type)
            if cli_args["only run type"] != None:
                title_hit_in_list = False
                for only_run_each in cli_args["only run type"]:
                    if only_run_each.lower() in conf["title"].lower():
                        title_hit_in_list = True
                        break
                if not title_hit_in_list:
                    pytest.skip("Type of test did not contain --only-run-type param (case insensitive)")
            # Same, but reversed for 'dont run':
            if cli_args["dont run type"] != None:
                for dont_run_each in cli_args["dont run type"]:
                    if dont_run_each.lower() in conf["title"].lower():
                        pytest.skip("Type of test contained --dont-run-type param (case insensitive)")
            
            ## Run the test:
            conf["method_pointer"](test_info, deepcopy(file_conf), deepcopy(cli_args), deepcopy(conf["variables"]))
            break
    assert found_test, "Could not find what test this block belongs to. {0}".format(error_msg)

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


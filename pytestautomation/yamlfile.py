import os # path
import pytest # File, Item
import warnings # warn

from .helpers import loadYamlFile, seperateKeyVal, skipTestsIfNecessary


PYTEST_CONFIG_INFO = None

def savePytestConfigInfo(info: dict):
    global PYTEST_CONFIG_INFO
    PYTEST_CONFIG_INFO = info

# Based on: https://docs.pytest.org/en/6.2.x/example/nonpython.html
class YamlFile(pytest.File):
    ## Default init used. Declared: self.parent, self.fspath

    def get_name(self):
        return os.path.basename(self.fspath)

    def collect(self):
        data = loadYamlFile(self.fspath, required=False)

        # Make sure it has tests:
        if "tests" not in data:
            warnings.warn(UserWarning("File is missing 'tests' key, skipping: '{0}'.".format(self.fspath)))
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

    # def repr_failure(self, excinfo):
    #     """Called when self.runtest() raises an exception."""
    #     return "\n".join(
    #         [
    #             "Test failed",
    #             "   Message: {0}:".format(excinfo.value)# {1}".format(excinfo.type.__name__, excinfo.value)
    #             # "   Test: '{0}'".format(self.test_info["title"]),
    #             # "   File: '{0}'".format(self.file_name)
    #             # "   Traceback: {0}".format(excinfo.tb),
    #             # "   Traceback: {0}".format(excinfo.traceback[-1:][0])
    #         ]
    #     )
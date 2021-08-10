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
        # Init your variables:
        super().__init__(test_info["title"], parent)
        self.file_name = parent.get_name()
        self.test_info = test_info

    def runtest(self):
        # Look for the right config to run off of:
        found_test = False
        for poss_test_type in PYTEST_CONFIG_INFO["test_types"]:
            # *IF* required_keys are declared, make sure the test only runs if THOSE keys are inside the test info:
            passed_key_check = True if "required_keys" not in poss_test_type or set(poss_test_type["required_keys"]).issubset(self.test_info) else False
            # *IF* required_in_title is declared, make sure the test only runs if it has the key in it's title:
            passed_title_check = True if "required_in_title" not in poss_test_type or poss_test_type["required_in_title"].lower() in self.test_info["title"].lower() else False

            # If you pass both filters, congrats! You can run the test:
            if passed_key_check and passed_title_check:
                # Save variables about finding the test:
                found_test = True
                self.test_type_name = poss_test_type["title"]
                # Check if you're supposed to run it:
                skipTestsIfNecessary(config=self.config, test_name=self.test_info["title"], file_name=self.file_name, test_type=poss_test_type["title"])
                # Run the test!!!
                # TODO: Add fixture support somehow: https://stackoverflow.com/questions/44959124/is-there-way-to-directly-reference-to-a-pytest-fixture-from-a-simple-non-test
                poss_test_type["method_pointer"](test_info=self.test_info, config=self.config, test_type_vars=poss_test_type["variables"])
                # You're done. Don't check ALL test types, only the FIRST match
                break
        assert found_test, "TEST TYPE NOT FOUND: Could not find which 'test types' element in pytest_config.yml to use with this test."

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        # Use built in cli arg:
        tbstyle = self.config.getoption("tbstyle", "auto")
        # If test_type_name got declared, use the name! Else test threw before it was hit:        
        try:
            test_type = self.test_type_name
        except AttributeError:
            test_type = "UNKNOWN"
        error_msg = "\n".join(
            [
                "Test failed",
                "   Test: '{0}'".format(self.test_info["title"]),
                "   File: '{0}'".format(self.file_name),
                "   Test Type: '{0}'".format(test_type),
            ]
        )
        # Add this section to the report:
        self.add_report_section("call", "yaml test info", error_msg)
        # Call the *real* report, and return that:
        return self._repr_failure_py(excinfo, style=tbstyle)

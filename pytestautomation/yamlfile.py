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
        # Return the error message for the test:
        return "\n"+"\n".join(
            [
                "Test failed",
                str(self._repr_failure_py(excinfo, style=tbstyle)),
                "   Test: '{0}'".format(self.test_info["title"]),
                "   File: '{0}'".format(self.file_name),
            ]
        # Default method: https://docs.pytest.org/en/6.2.x/_modules/_pytest/nodes.html#Collector.repr_failure
        # Docs on ExcInfo class itself: https://docs.pytest.org/en/6.2.x/reference.html#exceptioninfo
        )
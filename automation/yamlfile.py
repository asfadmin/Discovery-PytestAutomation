import os # path
import pytest # File, Item
import warnings # warn

from automation import helpers

# For type hints:
from typing import Generator
from _pytest._code.code import ExceptionInfo, TerminalRepr

PYTEST_CONFIG_INFO = {} # Populated in automation.plugin.pytest_sessionstart()

# Based on: https://docs.pytest.org/en/6.2.x/example/nonpython.html
class YamlFile(pytest.File):
    ## Default init used. Declared: self.parent, self.fspath

    def get_file_name(self) -> str:
        return os.path.basename(self.fspath)

    def collect(self) -> Generator[pytest.Item, None, None]:
        # Load the data. (required=False to NOT throw if it can't read).
        data = helpers.loadYamlFile(self.fspath, required=False)

        # Make sure it has tests:
        if data is None:
            return
        if "tests" not in data:
            warnings.warn(UserWarning(f"File is missing required 'tests' key: '{self.fspath}'. Skipping."))
            return

        # Collect the tests into your suite:
        for json_test in data["tests"]:
            test_info = helpers.seperateKeyVal(json_test, self.fspath, "test")
            yield YamlItem.from_parent(self, test_info=test_info)

class YamlItem(pytest.Item):

    def __init__(self, parent: YamlFile, test_info: dict):
        # Init your variables:
        super().__init__(test_info["title"], parent)
        self.file_name = parent.get_file_name()
        self.test_info = test_info

    def runtest(self) -> None:
        # Look for the right config to run off of:
        found_test = False
        for poss_test_type in PYTEST_CONFIG_INFO["test_types"]:
            # *ONLY IF* required_* is used, make sure the test only runs if it's check passes. If it's not used, default pass anyways:
            passed_key_check = True if "required_keys" not in poss_test_type or set(poss_test_type["required_keys"]).issubset(self.test_info) else False
            passed_title_check = True if "required_in_title" not in poss_test_type or poss_test_type["required_in_title"].lower() in self.test_info["title"].lower() else False

            # If you pass all filters, congrats! You can run the test:
            if passed_key_check and passed_title_check:
                found_test = True
                self.test_type_name = poss_test_type["title"]
                # Check if you're supposed to run it:
                helpers.skipTestsIfNecessary(config=self.config, test_name=self.test_info["title"], file_name=self.file_name, test_type=self.test_type_name)
                # Run the test!!!
                poss_test_type["method_pointer"](test_info=self.test_info, config=self.config, test_type_vars=poss_test_type["variables"])
                # You're done. Don't check ALL test types, only the FIRST match
                break
        assert found_test, "TEST TYPE NOT FOUND: Could not find which 'test_types' element in pytest-config.yml to use with this test."

    def repr_failure(self, excinfo: ExceptionInfo) -> TerminalRepr:
        """Called when self.runtest() raises an exception."""
        # If test_type_name got declared, use the name! Else test threw before it was hit:        
        try:
            test_type = self.test_type_name
        except AttributeError:
            test_type = "UNKNOWN"
        error_msg = "\n".join(
            [
                "Test failed",
                f"   Test: '{self.test_info['title']}'",
                f"   File: '{self.file_name}'",
                f"   Test Type: '{test_type}'",
            ]
        )
        # Add this section to the report:
        self.add_report_section("call", "yaml test info", error_msg)
        # Get built in cli arg, controls how verbose to make the report:
        tbstyle = self.config.getoption("tbstyle", "auto")
        # Call the *real* report, and return that:
        return self._repr_failure_py(excinfo, style=tbstyle)

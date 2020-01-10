import yaml
import conftest as helpers

# Lets you import files in the directory behind this one:
import sys, os
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(1, project_root)
from tests import pytest_managers as tests



file_config = os.path.join(project_root, "tests", "pytest_config.yml")

try:
	file_config = open(file_config, "r")
	file_config = yaml.safe_load(file_config)
except (OSError, IOError):
    assert False, "Error opening yaml {0}. Does it exist?".format(project_root)
except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
    assert False, "Error parsing yaml {0}. Error: {1}.".format(project_root, str(e))

test_list = helpers.loadTestsFromDirectory(project_root, recurse=True)
print(test_list)
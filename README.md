# Pytest Automation

[![image](https://img.shields.io/pypi/v/pytest-automation.svg)](https://pypi.python.org/pypi/pytest-automation)

### **Add to an existing project**:
1) Run:

```bash
python3 -m pip install pytest-automation
```

2) Add the two required files to your project. (Listed in next step).

### **Required Files**:

It doesn't matter where in your project these exist, but names are case-sensitive, and *exactly* one of each can exist.

- ### pytest_config.yml:

After all the tests get loaded, this controls what method to call for each individual test.

Example:

```yaml
test_types:

- For running addition tests:
    required_keys: ["x_add", "y_add"]
    method: test_PythonsAddition

- For running factorial tests:
    required_keys: factor_num
    required_file: test_factorials.yml
    method: test_NumpysFactor
    variables:
      throw_on_negative: False
```

- For every test, it tries to match the keys in the test to 'required_\*' options, **from top to bottom**. If matched, it will try to load the declared method from 'pytest_managers.py' (The *other* required file). 

- The 'variables' key gets passed to every test that 'test block' runs. Here, the first test type passes None, and the second passes in a dict { throw_on_negative: False }. Useful for passing in urls, endpoints, etc that might change often for that type of test.

- 'required_keys' will check if the test block contains ALL the keys listed to run.

- 'required_file' needs the full name of the file (NOT the path). Can be a list of file names.

- Neither required_keys or required_files are "required" to be in a test block. If you have neither, then EVERY test that makes it that far will run with that method, and no tests will continue to the test types after it. Likewise, if BOTH are in a block, then they BOTH must hold true to run the test.

- ### pytest_managers.py:

Contains the code that gets executed, for each individual yml test. 

Example:

```python
from custom_math import run_add_test, run_fact_test

# The methods name matchs the 'method' key in 'pytest_config.yml'
def test_PythonsAddition(test_info, file_conf, cli_args, test_vars):
	run_add_test(test_info, file_conf, cli_args, test_vars)

def test_NumpysFactor(test_info, file_conf, cli_args, test_vars):
	run_fact_test(test_info, file_conf, cli_args, test_vars)
```

- Recommended to import files (i.e custom_math above), that themselves contain the *real* test suite. Only to keep this file short.

NOTE: Looking on if there's an optional way to pass in params now! Come back and update!! (Hopefully will find a way to not "require" any of them...)

- test_info: A dict, containing all the contents of the yml test. The title of the test gets moved into the test, under the key 'title'.

- file_conf: (DEPRECATED!!! Maybe...) If the yml file holding the tests has contents outside of the 'tests' block, They'll get added here ONLY for the tests inside that file.

- cli_args: Holds what commands are used when running tests. (--only-run, --dont-run, etc. are here too, but I already skip the tests if those are used, before these methods are called).

- test_vars: If you use 'variables' in the pytest_config.py, whatever you set it to gets set to this (Dict, list, etc). 

### **Running the Tests**:

```bash
pytest <pytest args here> . <custom args here>
```
- Common pytest args:
   - '-n INT' => (By itself), The number of threads to use. Make sure tests are thread-safe. (Default = 1).
   - '-s' => If python prints anything, show it to your console.
   - '-x' => Quit as soon as the first test fails
   - (-v|-vv|-vvv) => How much info to print for each test

- Custom args (Filter what tests to run):
    - '--only-run-name, --dont-run-name' (--on/--dn) => (Can use multiple times) Looks at the name of each test to determine if it needs to run.

    - '--only-run-file', '--dont-run-file' (--of/--df) => (Can use multiple times) Determines if ALL tests in a file gets skipped, based on name of file. (Full name of file, but *not* the path).

    - '--only-run-type', '--dont-run-type' (--ot/--dt) => (Can use multiple times) Looks at the title in pytest_config.yml. Tries to see if what is passed to these, is within the title.


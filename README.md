# Pytest Automation

### Add to an existing project:
1) Add this repo as a submodule, in the root of your project:
```bash
        git submodule add -b prod git@github.com:asfadmin/Discovery-PytestAutomation.git
```

2) Pull the contents of the repo. (Also how you pull updates).
```bash
        git pull --recurse-submodules
        git submodule update --init --recursive --remote # Use '--remote' to pull any changes made to the testing repo since you added it.
```

3) Add the required files below to your project. (Doesn't matter where, but names are case-sensitive, and only one  of each can exist).

### Required Files:
It doesn't matter where in your project these exist, but names are case-sensitive, and *exactly* one of each can exist.
###### pytest_config.yml:
After all the tests get loaded, this controls what tests get sent where, based on the dict keys within each test.
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
For every test, it tries to match the keys in the test to 'required_*' options, **from top to bottom**. If matched, it will try to load the declared method from 'pytest_managers.py' (Another required file). 
The 'variables' key gets passed to every test that 'test block' runs. Here, it passes in a dict { throw_on_negative: False }. Useful for passing in urls, endpoints, etc that might change often for that type of test.
'required_keys' will check if the test block contains ALL the keys listed to run. required_file needs the full name of the file (NOT the path). Both can require multiple in the same test, by making it a list, like in the first example above. You can also use both in the same block, and it will ONLY run tests that are both in that file, AND have those keys. If you use neither one, then ANY test that makes it that far down the list, will run there. This means if you have any test_type below the one without either 'required_*' key, it will never run.

Pre/post hooks:
For running a method before/after the **entire** suite, you can add the following to pytest_config.yml:
```yaml
test_hooks:
  before_suites: pytest_start
  after_suites: pytest_end
```
You can use any number of these. This will search pytest_managers.py for a method 'pytest_start' when the suite kicks up, and runs it. Dito for after_suites, but after everything finishes. The after_suites method accepts an optional positional parameter that's the exit code of the run.

##### pytest_managers.py:
Contains the code that gets executed, for each individual yml test. 
Example:
```python
from custom_math import run_add_test, run_fact_test
# The methods match what is in 'pytest_config.yml'
def test_PythonsAddition(test_info, file_conf, cli_args, test_vars):
	run_add_test(test_info, file_conf, cli_args, test_vars)

def test_NumpysFactor(test_info, file_conf, cli_args, test_vars):
	run_fact_test(test_info, file_conf, cli_args, test_vars)
```
Here, I have each method call the 'real' test code, just to keep this file less cluttered, and lets you split tests to different files for better organization. The four variables it accepts are all required, and order-dependant.

- test_info: A dict, containing all the contents of the yml test. The title of the test gets moved into the test, under the key 'title'.
- file_conf: If the yml file holding the tests has contents outside of the 'tests' block, They'll get added here ONLY for the tests inside that file.
- cli_args: Holds what commands are used when running tests. (--only-run, --dont-run, etc. are here too, but I already skip the tests if those are used, before these methods are called).
- test_vars: If you use 'variables' in the pytest_config.py, whatever you set it to gets set to this (Dict, list, etc). 

Adding a variable to 'file_conf' vs 'test_vars' depends on how you organized your tests. A single yml file can hold multiple different types of tests inside it's 'tests' key. If you have a yml of 'known-bugs', you might want specific variables for those tests, whereas if you want every factorial test to have it exposed, put it in 'test_vars'.

### Running the Tests:
NOTE: As of writting this, you can only run the suite if you're in the root of the PytestAutomation module, but I'm looking at ways to change this.

```bash
pytest <pytest args here> . <custom args here>
```
- Common pytest args:
   - '-n INT' => (By itself), The number of threads to use. Make sure tests are thread-safe. (Default = 1).
   - '-s' => If python prints anything, show it to your console.
   - '-x' => Quit as soon as the first test fails
   - (-v|-vv|-vvv) => How much info to print for each test

- Custom args:
    - '--api [local|dev|test|prod]' => Which api to hit. If input doesn't match these, it'll treat input as the url itself.  
    - '--only-run-name, --dont-run-name' (--on/--dn) => (Can use multiple times) Looks at the name of each test to determine if it needs to run.
    - '--only-run-file', '--dont-run-file' (--of/--df) => (Can use multiple times) Determines if ALL tests in a file gets skipped, based on name of file. (Full name of file, but *not* the path).
    - '--only-run-type', '--dont-run-type' (--ot/--dt) => (Can use multiple times) Looks at the title in pytest_config.yml. Tries to see if what is passed to these, is within the title.

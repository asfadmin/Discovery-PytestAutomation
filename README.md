# Pytest Automation

[![image](https://img.shields.io/pypi/v/pytest-automation.svg)](https://pypi.python.org/pypi/pytest-automation) [![CodeFactor](https://www.codefactor.io/repository/github/asfadmin/discovery-pytestautomation/badge/stable)](https://www.codefactor.io/repository/github/asfadmin/discovery-pytestautomation/overview/stable)

For automating test creation. This plugin lets you send a list of tests (arguments defined in yaml's), to python methods. For creating an agile test suite.

This plugin is compatible to run alongside vanilla pytest tests, without interfering with them. The custom CLI arguments for this plugin won't affect those tests (Including --skip-all).

----

- [How to setup the Test Suite](#how-to-setup-the-test-suite)
  - [1) Install the plugin](#1-install-the-plugin)
  - [2) Add both required files](#2-add-both-required-files)
    - [pytest-config.yml](#pytest-configyml)
    - [pytest-managers.py](#pytest-managerspy)
  - [3) Write the yaml tests](#3-write-the-yaml-tests)
    - [yaml requirements](#yaml-requirements)
    - [writing yaml tests example](#writing-yaml-tests-example)
    - [yaml test philosophy](#yaml-test-philosophy)
  - [4) Using conftest.py for extra Flexibility](#4-using-conftestpy-for-extra-flexibility)
    - [Adding CLI Options](#adding-cli-options)
    - [Running scripts before/after the Suite](#running-scripts-beforeafter-the-suite)
    - [Full list of Hooks](#full-list-of-hooks)
- [How to run tests](#how-to-run-tests)
  - [Running the Tests](#running-the-tests)
- [How to Build from Source](#how-to-build-from-source)

----

## How to setup the Test Suite

### 1) Install the plugin

Run the following:

```bash
python3 -m pip install pytest-automation
```

### 2) Add both required files

It doesn't matter where in your project these exist, but names are case-sensitive, and **exactly** one of each should exist. If you need to ignore a sub-directory with it's own pytest suite, use `--ignore <dir>` (More info on ignoring [here](#common-pytest-cli-args)).

- #### **pytest-config.yml**

    This file defines where each individual [yml test](#3-write-the-yaml-tests) gets sent, to which method in the [pytest-managers.py](#pytest-managerspy) file.
    
    This also allows you to have multiple types of tests in the same file. (Useful for example, having a test_known_bugs.yml you can exclude from pipelines).

    This file is required to have one `test_types` key. This holds a list, of each type of test (or `test type`) you'd like in your suite. Each element in the list, is in the format {"test title": {all_test_info}} (Shown in [this example](#pytest-configyml-example) below).

    #### **pytest-config.yml example**:
    ```yaml
    # Contents of pytest-config.yml
    test_types:

    - For running addition tests:
        required_keys: ["x_add", "y_add"]
        method: test_PythonsAddition

    - For running factorial tests:
        required_keys: factor_num
        required_in_title: test-factor
        method: test_NumpysFactor
        variables:
            throw_on_negative: False
    ```
    Possible filters in each `test type`:

    - `required_keys`: The yml test must contain ALL these keys to run with this `test type`.

    - `required_in_title`: Check if the test title contains this string (case insensitive). NOTE: With basic values, it's easy to accidentally match new tests later on. Best practice is to use something like "test-[something]", instead of just "[something]". 

    Each [yml test](#3-write-the-yaml-tests) will go through the `test_types` list *in order*, and the following things will happen:

    - ONLY keys that are declared will be checked. Also you can have multiple `required_*` keys in the same `test type`, and they ALL have to match for the test to run.

        - Note: This means if it has *NO* `required_*` keys, ALL tests will match it, so *no* tests will continue pass that `test type`.
    
    - If the test is matched to that type, the function under `method` will be looked for in [pytest-managers.py](#pytest-managerspy) and called.

    - If NO `test type` is matched, that test will fail, and the next will run.

    In the pytest-config [example](#pytest-configyml-example) above, the test_PythonsAddition will only be called, if that yml test contains both the x_add and y_add keys. With the test_NumpysFactor, it'll only be called if that yml test has the factor_num key, AND it's in the test_factorials.yml file.

    #### **Test Type Variables**:

    In the pytest-config [example](#pytest-configyml-example) above, you can see the following key in the second `test type`:

    ```yaml
    variables:
        throw_on_negative: False
    ```

    This `variables` key is optional. It'll pass it's contents into each [pytest-managers](#pytest-managerspy) method, under the `test_type_vars` param. This is useful for declaring url's, endpoints, etc. More info on what arguments get passed to the `method` [here](#args-passed-into-each-test).

- #### **pytest-managers.py**

    When a [yml test](#3-write-the-yaml-tests) is matched with [test type](#pytest-configyml), that test type's `method` is imported from this file, and ran.

    #### **pytest-managers.py example**
    ```python
    # Contents of pytest-managers.py
    from custom_add import run_add_test
    from custom_factor import run_fact_test

    # The methods here matchs the 'method' key in 'pytest-config.yml' example. (Required)

    def test_PythonsAddition(**args):
	    run_add_test(**args)
        # *OR* just run test here:
        test_info = args["test_info"]
        assert test_info["x_add"] + test_info["y_add"] == test_info["answer"]

    def test_NumpysFactor(**args):
        run_fact_test(**args)
        # *OR* just run test here:
        test_factor = args["test_info"]["factor_num"]
        assert factor(test_factor) == args["test_info"]["answer"]
    ```

    Like with the first line of each method, it's *recommended* to have the testing code in another file, and just call it from this one. This helps keeps the suite organized for longer test methods. Even if you import other methods, ONLY the methods defined in this file can be loaded from the `method` key in [pytest-config.yml](#pytest-configyml).

    #### **Args passed into each Test**

    Each test in pytest-managers.py should only accept `**args` as their one param. That'll allow the plugin to add extra keys in the future, without breaking older tests. The following keys are currently guaranteed:

    - **`config`**: A [pytest config (ext link)](https://docs.pytest.org/en/6.2.x/reference.html?highlight=config#config) object. For interacting with pytest itself (i.e getting which [cli options](#adding-cli-options) were used when running the suite)

    - **`test_info`**: The parameters from the yml file. This is passed into the python manager, and what makes each test unique. More info [here](#3-write-the-yaml-tests).

    - **`test_type_vars`**: How to declare variables for a [test type](#pytest-configyml), and not have them hard-coded/duplicated in each test. (i.e. what api endpoint to target). More info [here](#test-type-variables).

### 3) Write the yaml tests

This is where you define each individual test. Each test is matched to a [test type](#pytest-configyml), then ran. 

#### **yaml requirements**:

- All yaml names must start with "test_", and end with either ".yml" or ".yaml". 

- The list of tests, must be under a **SINGLE** `tests` key, inside the file. If more than one key exists, they'll override each other, and you won't run all your tests.

- Each test in the list, is a single dict of the format {"test title": {ALL_TEST_INFO}}

#### **writing yaml tests example**:

```yaml
# Contents of test_MyCustomMath.yml
# These examples match the "pytest-config.yml" example, with required_keys above. 

tests:
- Basic addition test:
    x_add: 5
    y_add: 7
    answer: 12

- Factorial Basic test:
    factor_num: 4
    answer: 24

- test-factor Factorial special case zero:
    factor_num: 0
    answer: 1

- Negative addition test:
    x_add: 5
    y_add: -7
    answer: -2
```

The first test gets matched to the addition `test type` in the pytest-config [example](#pytest-configyml-example), containing the two required keys. 

The second and *would* get matched to the factorial test, *except* it doesn't have "test-factor" in it's title, like `required_in_title` says it should, so it doesn't get matched to *anything* and fails.

The third test *does* have "test-factor" in it's title, so it runs as normal. 

The fourth test gets matched to the addition `test type`, so it runs with that `method` in the [pytest-config.yml](#pytest-configyml).

**IMPORTANT NOTE**: Before passing each yml test to their `method`, the plugin will move the title *into* the info, with `title` becoming key. So the `title` key is reserved:

```yaml
# Before passing into the test, this test info:
- Negative addition test:
    x_add: 5
    y_add: -7
    answer: -2
# Will automatically become:
- title: Negative addition test
  x_add: 5
  y_add: -7
  answer: -2
# To make accessing each item easier to access.
```

(Example on how to access the `test_info` values [here](#pytest-managerspy-example)).

#### **yaml test philosophy**:

One key idea behind organizing tests into yamls, is you can move each individual yml test between files, and the test will still behave as expected.

- This means you can have "test_known_bugs.yml" to exclude from build pipelines, or "test_prod_only.yml" that only gets executed against your prod environment. etc.

- This also means we can't decide which `test type` to run a test with, based on what file it's in. Otherwise, as soon as you moved a test from this file, to "known_bugs.yml", it's behavior might change. 

### 4) Using `conftest.py` for extra Flexibility

You're able to use [pytest hooks (ext link)](https://docs.pytest.org/en/6.2.x/reference.html#hooks) to run commands before the suite, add CLI options, etc; by declaring them in a `conftest.py` file inside your project. 

(**NOTE**: Fixtures not currently supported, but hopefully coming soon!)

#### **Adding CLI Options**

Add the [pytest_addoption (ext link)](https://docs.pytest.org/en/6.2.x/reference.html#pytest.hookspec.pytest_addoption) hook for declaring CLI arguments.

```python
# Contents of conftest.py

def pytest_addoption(parser):
    # addoption is built on top of argparse, same syntax:
    parser.addoption("--api", action="store", default="local",
        help = "Which API to hit when running tests (LOCAL/DEV/TEST/PROD, or url).")

    # Add other 'parser.addoption' calls here for each argument
```

Then each tests can look at what was the user passed in, through the `config`.

```python
# Contents of some test file, called by pytest-managers.py

def test_CheckQueries(**args):
    api = args["config"].getoption("--api")

    # ... Continue to run whatever checks after this ...
```

#### **Running scripts before/after the Suite**

Add the [pytest_sessionstart (ext link)](https://docs.pytest.org/en/6.2.x/reference.html#pytest.hookspec.pytest_sessionstart) or [pytest_sessionfinish (ext link)](https://docs.pytest.org/en/6.2.x/reference.html#pytest.hookspec.pytest_sessionfinish) hooks for adding startup/tear down logic.

```python
# Contents of conftest.py

def pytest_sessionstart(session):
    # Maybe you need a directory for dumping temp files:
    temp_dir = "some/tmp/dir"
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)

def pytest_sessionfinish(session, exitstatus):
    # Maybe send a email if the suite fails
    pass
```

#### **Full list of Hooks**

You can find the full list [here (ext link)](https://docs.pytest.org/en/6.2.x/reference.html#hooks).

----

## How to run tests

### **Running the Tests**:

```bash
pytest <pytest and plugin args here> <PATH> <custom conftest args here>
# Example:
pytest -n auto -s -tb short --df known_bugs . --api devel
```
- #### **Common pytest CLI args**:
   - `-n int` => The number of threads to use. Make sure tests are thread-safe. (Default = 1, install [pytest-xdist (ext link)](https://pypi.org/project/pytest-xdist/) to use).

   - `-s` => If python prints anything, show it to your console.

   - `-x` => Quit as soon as the first test fails

   - (`-v`|`-vv`|`-vvv`) => How much info to print for each test

   - `--tb ("short" | "long" | ...)` => How much error to print, when a test fails. (Other options available, more info [here (ext link)](https://docs.pytest.org/en/6.2.x/usage.html#modifying-python-traceback-printing))

   - `--ignore DIR` => Ignore this directory from your suite. Works both with vanilla pytest tests, and pytest-automation files. Useful if you pull another repo into yours, and it has it's own test suite. (More info [here (ext link)](https://docs.pytest.org/en/6.2.x/example/pythoncollection.html#ignore-paths-during-test-collection)).

- #### **Custom pytest-automation args**:

    Filter what tests to run:

    - `--only-run-name str`, `--dont-run-name str` (`--on str`/`--dn str`) => (Can use multiple times) If the name of the test *contains* this value, only/don't run accordingly.

    - `--only-run-file str`, `--dont-run-file str` (`--of str`/`--df str`) => (Can use multiple times) If the file the test is in *contains* this value, only/don't run accordingly.

    - `--only-run-type str`, `--dont-run-type str` (`--ot str`/`--dt str`) => (Can use multiple times) Looks at the title in [pytest-config.yml](#pytest-configyml-example), and if it *contains* this value, only/don't run accordingly.

    - `skip-all`: Skips all pytest-automation yaml tests. (Doesn't skip vanilla pytest methods).

-  #### **PATH**:
    - The path to start collecting tests / `conftest.py` files from.

    - Normally just "." for current directory. (i.e. 'pyest . ')

- #### **Custom conftest CLI args**:

    Any arguments **you** define in your projects `conftest.py` file. More info [here](#adding-cli-options).

----

## How to Build from Source

#### 1) Create your environment:

```bash
# Upgrade pip to latest and greatest
python3 -m pip install --upgrade pip
# Install tool for creating environments
python3 -m pip install virtualenv
# Create the environment
virtualenv --python=python3 ~/PytestAuto-env
# Jump inside it. (You'll need to run this for each new shell)
source ~/PytestAuto-env/bin/activate
```

 - You should see your terminal start with "(PytestAuto-env)" now.

#### 2) Install the required files to build:

 ```bash
 # Because of the --python=python3 above, you can now just run 'python':
 python -m pip install setuptools wheel twine packaging
 # Install the files needed to run setup.py:
 python -m pip install <Path-to-this-repo-root>/requirements.txt
 ```

#### 3) Install it:

- Or run this after each change to the source.

```bash
# NOTE: The "--upgrade" is needed incase it's already installed.
#  (i.e. Don't use cached version).
python -m pip install --upgrade <Path-to-this-repo-root>
```

----
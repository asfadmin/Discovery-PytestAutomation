# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/) 
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


<!--
## Example template!!

## [v<VERSION>](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v<OLD>...v<NEW>)

### Added:
-

### Changed:
-

### Fixed:
- 

### Removed:
-

-->

------

## [v2.0.1](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v2.0.0...v2.0.1)

### Fixed:
- Pass **copies** of params into the test, so that they can't modify the params before `repr_failure` is called on test cleanup.

------

## [v2.0.0](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v1.1.2...v2.0.0)

### Breaking Change:
- Upgraded to pytest-7, which included [this deprecation](https://docs.pytest.org/en/7.0.x/deprecations.html#fspath-argument-for-node-constructors-replaced-with-pathlib-path). **Plugin will now only work with pytest>=7.0.0**.

### Fixed:
- UserWarning: Unknown distribution option: 'use_scm_version', by declaring it in pyproject.toml instead.
- Stopped plugin from searching for `pytest-managers.py` and `pytest-config.yml`, in directories that match [pytest's norecursedirs](https://docs.pytest.org/en/6.2.x/reference.html?highlight=norecursedirs#confval-norecursedirs) config variable. This stops a duplicate `pytest-managers.py` in `build`, from halting the entire suite for example.
- Updated packages in `requirements.txt` to latest and greatest. Checked nothing broke from doing so.

### Removed:
- Removed `packaging` package from pyproject.toml, and requirements.txt

------

## [v1.1.2](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v1.1.0...v1.1.2)

### Fixed:
- Populate `__version__` with importlib instead of setuptools_scm, to let people use package without git. (v1.1.1 wont work if installed from PyPI becasue of this). Also removes setuptools_scm dependency after build.

------

## [v1.1.0](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v1.0.0...v1.1.0)

### Changed:
- Improved error checking and error messages, for misformed yml tests and `test_types`. Removed the extra warning when plugin collects an empty test_*.yml file.

- Moved code to figure out version, from `setup.py` to `automation/__init__.py`. This lets me populate `__version__` from there.

### Removed:
- Removed automatically ignoring git submodules. Can only ignore files loaded by this plugin and not vanilla pytest tests anyways, so switching to pytest's `--ignore <dir>` flag for this functionality.

- Figured out how to remove the single global statement, by changing how each file imports one another.

------

## [v1.0.0](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v0.0.1...v1.0.0)

First major release!

### Added:
- Changelog action, to guantee this file is updated on releases.

- Added with `required_in_title` as an option to each `test_types`, that checks it's value against the title of each test. (Replacement for `required_files`. More info [here](https://github.com/asfadmin/Discovery-PytestAutomation/tree/stable#pytest-configyml-example)).

- Python `type hints` to most functions.

- Instructions on installing package from source in `README.md`

### Changed:
- `pytest_managers.py` and `pytest_config.yml` have been renamed to `pytest-managers.py` and `pytest-config.yml`. This is because '_' is inconsistent between Markdown anchors, but '-' isn't.

### Removed:
- Removed `required_files` key as an option from `test_types`. Decided each test should run exactly the same, regardless of what file it's in. (Allows you to have a "known_bugs.yml" you can move tests in/out of).

### Fixed:
- Empty test_*.yml's used to stop test suite from running, since the parser returned `None` instead of a empty string.

------

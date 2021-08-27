# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/) 
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


<!--
## Example template!!

## [version](https://github.com/asfadmin/Discovery-PytestAutomation/compare/vOLD...vNEW)

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

## [v1.0.0](https://github.com/asfadmin/Discovery-PytestAutomation/compare/v0.0.1...v1.0.0)

First major release!

### Added:
- Changelog action, to guantee this file is updated on releases.

- Added with `required_in_title` as an option to each `test_types`, that checks it's value against the title of each test. (Replacement for `required_files`. More info [here](https://github.com/asfadmin/Discovery-PytestAutomation/tree/stable#pytest-configyml-example)).

### Changed:
- `pytest_managers.py` and `pytest_config.yml` have been renamed to `pytest-managers.py` and `pytest-config.yml`. This is because '_' is inconsistent between Markdown anchors, but '-' isn't.

### Removed:
- Removed `required_files` key as an option from `test_types`. Decided each test should run exactly the same, regardless of what file it's in. (Allows you to have a "known_bugs.yml" you can move tests in/out of).

### Fixed:
- Empty test_*.yml's used to stop test suite from running, since the parser returned `None` instead of a empty string.

------
import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pytest-automation",
    use_scm_version=True,
    description="pytest plugin for building a test suite, using YAML files to extend pytest parameterize functionality.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alaska Satellite Facility Discovery Team",
    author_email="uaf-asf-discovery@alaska.edu",
    packages=["automation"],
    url="https://github.com/asfadmin/Discovery-PytestAutomation",
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["pytest-automation = automation.plugin"]},
    # custom PyPI classifier for pytest plugins
    classifiers=[
        "Framework :: Pytest",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Testing"
    ],
    install_requires=[
        'pytest',
        'PyYAML',
    ],
    license='BSD',
    license_files=('LICENSE',),


    ## After creating test suite, figure out if these keys are useful:
    #test_suite='???',
    #tests_require=['???'],
)
import conftest as helpers
import sys, os, pytest

# project root = One dir back from the dir this file is in
project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
main_config = helpers.getConfig()
all_tests = helpers.loadTestsFromDirectory(project_root, recurse=True)

# For each item in the list, run it though the suite:
@pytest.mark.parametrize("test", all_tests)
def test_main(test, cli_args):
	test_info = test[0]	# That test's info
	file_conf = test[1] # Any extra info in that test's yml
	# Skip the test if needed:
	helpers.skipTestsIfNecessary(test_info["title"], file_conf["yml name"], cli_args)

	# pass the values to the right function:
	found_test = False
	for conf in main_config["test_types"]:
		# If all of the required keys are in the test, you found it:
		if set(conf["required_keys"]).issubset(test_info):
			found_test = True
			# Run the test:
			# (NOT catching TypeError because if something *in* that test throws it, this would still catch...)
			# try:
			conf["method_pointer"](test_info, file_conf, cli_args)
			# except TypeError:
				# assert False, "Method '{0}' needs to accept three parameters. (test_info, file_config, cli_args).".format(conf["method"])
			break
	# If you never matched to a function, error out.
	assert found_test, "Cannot determine test type. Test: {0}. File: {1}.".format(test_info["title"], file_conf["yml name"])



# A simple class to improve error outputs from tests:

class error_msg():
    def __init__(self):
        self.error_msgs = []

    # Lets you add variables values as the test runs
    # max_length = Number of chars allowed in error msg. (-1 for ALL)
    # new_block = If value should be on it's own line, under key
    def append_report(self, variable, value, max_length=500, new_block=False):
        # Incase they're ints or something:
        variable, value = str(variable), str(value)
        # If negative, have no limit:
        max_length = len(value) if max_length < 0 else max_length
        
        # Start building the report for this variable:
        msg = "\n - "+variable+": "
        msg += "\n" if new_block else ""
        msg += value[:max_length]
        # Add the 'truncated' tag if nessessary:
        if len(value) > max_length:
            msg += "\n -(Truncated. Full value is {0} long.)".format(len(value))
        self.error_msgs.append(msg)

    # View/format the entire report (if a test fails):
    def get_info(self, fail_reason):
        report = "{0}".format(fail_reason)
        report += "".join(self.error_msgs)
        return report

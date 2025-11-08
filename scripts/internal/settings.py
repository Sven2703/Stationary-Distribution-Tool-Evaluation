import os

from .utility import *
from .tools import greatspn, sds, storm, prism

class Settings():
    def __init__(self, task, results_directory):
        self.json_data = OrderedDict()
        self.json_data["task"] = str(task)
        self.json_data["filtered-paths"] = [os.path.realpath(sys.path[0]) + "/", os.path.expanduser("~") + "/"]
        # binary defaults
        for tool in [greatspn, sds, storm, prism]:
            self.json_data[tool.get_name() + "-executable"] = tool.get_default_executable()

        # set and create directories
        self.json_data["benchmarks-directory"] = "$ARTIFACT_DIR/benchmarks/"
        self.json_data["results-directory"] = results_directory
        self.json_data["logs-directory"] = os.path.join(self.results_dir(), "logs")
        self.json_data["export-directory"] = os.path.join(self.results_dir_logs(), "exports")
        self.json_data["plots-directory"] = os.path.join(self.results_dir(), "plots")
        self.json_data["tables-directory"] = os.path.join(self.results_dir(), "tables")


    def test_result_dirs(self):
        if not os.path.exists(set_artifact_dir(self.results_dir())):
            AssertionError("Directory '{}' does not exist".format(self.results_dir()))
        if not os.path.exists(set_artifact_dir(self.results_dir_logs())):
            AssertionError("Directory '{}' does not exist".format(self.results_dir_logs()))
        if not os.path.exists(set_artifact_dir(self.results_dir_tables())):
            AssertionError("Directory '{}' does not exist".format(self.results_dir_tables()))
        if not os.path.exists(set_artifact_dir(self.results_dir_plots())):
            AssertionError("Directory '{}' does not exist".format(self.results_dir_plots()))
        if not os.path.exists(set_artifact_dir(self.results_dir_exports())):
            AssertionError("Directory '{}' does not exist".format(self.results_dir_exports()))

    def ensure_result_dirs(self):
        ensure_directory(self.results_dir_exports())
        ensure_directory(self.results_dir_logs())
        ensure_directory(self.results_dir_tables())
        ensure_directory(self.results_dir_plots())


    def results_dir(self):
        """ Retrieves the results directory. """
        return self.json_data["results-directory"]

    def task(self):
        """ Retrieves the results directory. """
        return self.json_data["task"]

    def benchmark_dir(self):
        """ Retrieves the directory where the benchmarks lie. """
        return self.json_data["benchmarks-directory"]

    def results_dir_logs(self):
        """ Retrieves the directory in which the tool logs are stored."""
        return self.json_data["logs-directory"]

    def results_dir_exports(self):
        """ Retrieves the directory in which the .json files containing the EVTs results are stored."""
        return self.json_data["export-directory"]

    def results_dir_plots(self):
        """ Retrieves the filename to which the tool execution results for scatter plots are stored. """
        return self.json_data["plots-directory"]

    def results_dir_tables(self):
        """ Retrieves the directory to which the tool execution result table is stored. """
        return self.json_data["tables-directory"]

    def filtered_paths(self):
        """ returns a list of paths (e.g. home directory) that should be filtered from commands in logfiles """
        return self.json_data["filtered-paths"]

    def tool_executable(self, toolname):
        """ Retrieves the path to the tool's executable."""
        return self.json_data[toolname.lower() + "-executable"]

    def input_tool_executable(self, toolname):
        """ Asks the user to enter a path to the tool's executable."""
        default_binary_dir = ""
        response = input("Enter path to {} executable [{}]: ".format(toolname, self.tool_executable(toolname)))
        if response != "":
            self.json_data[toolname + "-executable"] = response

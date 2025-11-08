from collections import OrderedDict
from .execution import Execution
import os

class Invocation(object):

    def __init__(self, invocation_json = None):
        """ Creates either an empty invocation that can be filled using 'add command' or an invocation from an existing json representation."""
        self.command = ""
        self.note = ""
        self.tool = ""
        self.configuration_id = ""
        self.benchmark_id = ""
        self.precision = ""
        self.solver_id = ""
        self.time_limit = None
        self.export = None

        self.export_value_file = None # not saved

        if invocation_json is not None:
            self.benchmark_id = invocation_json["benchmark-id"]
            self.configuration_id = invocation_json["configuration-id"]
            self.solver_id = invocation_json["solver-id"]
            self.tool = invocation_json["tool"]
            self.export = invocation_json["export"]
            self.note = invocation_json["invocation-note"]
            self.time_limit = float(invocation_json["time-limit"])
            self.precision = invocation_json["precision"]

            self.command = invocation_json["command"]
            if self.command == "":
                raise AssertionError("No command defined for the given invocation")


    def get_identifier(self):
        if "." in self.tool: raise AssertionError("Tool name '{}' contains a '.'. This is problematic as we want to infer the tool name from the logfile name.")
        if "." in self.configuration_id: raise AssertionError("Configuration id '{}' contains a '.'. This is problematic as we want to infer the configuration id from the logfile name.")
        if "." in self.solver_id: raise AssertionError("Eqsolver id '{}' contains a '.'. This is problematic as we want to infer the solver id from the logfile name.")
        return self.tool + "." + self.configuration_id + "." + self.solver_id + "." + ("ignored" if self.precision == "ignored" else str(self.precision)) + "." + self.benchmark_id
        
    def set_command(self, command):
        if not isinstance(command, str):
            raise AssertionError("The given command is not a string!")
        self.command = command

    def to_json(self):
        return OrderedDict([("benchmark-id", self.benchmark_id),
                            ("tool", self.tool),
                            ("configuration-id", self.configuration_id),
                            ("solver-id", self.solver_id),
                            ("export", self.export),
                            ("invocation-note", self.note),
                            ("command", self.command),
                            ("time-limit", self.time_limit),
                            ("precision", "ignored" if self.precision == "ignored" else float(self.precision))])

    def execute(self):
        execution = Execution(self)
        execution.run(True) # with warm-up run!
        return execution



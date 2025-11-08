from collections import OrderedDict

class Solver(object):

    def __init__(self, solver_json = None, id = None, note= None, command = None):
        """ Creates either an empty solver or an solver from an existing json representation."""
        self.command = command
        self.note = note
        self.identifier = id
        if solver_json is not None:
            self.command = solver_json["command"]
            if "." in solver_json["solver-id"] or ":" in solver_json["solver-id"]:
                raise AssertionError("Characters '.' and ':' are not allowed in configuration identifier {}".format(solver_json["solver-id"]))
            self.identifier = solver_json["solver-id"]
            self.note = solver_json["solver-note"]
 
    def to_json(self):
        return OrderedDict([("solver-id", self.identifier), ("solver-note", self.note), ("command", self.command)])



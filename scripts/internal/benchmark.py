# -*- coding: utf-8 -*-
from .utility import *

class Benchmark(object):
    """ This class represents a benchmark, that is
        * a model
        * an instantiation of file and open parameters
    """
    def __init__(self, settings, index_json, model_file_index, open_parameter_index, property):
        """
        :param index_json: The json structure of the 'index.json' file of the model
        :param model_file_index: The index of the model file entry within the "files" entry in the json structure
        :param open_parameter_index: The index of the open parameter instantiation within the "open-parameter-vaules" entry of the file entry
        """
        self.settings = settings
        self.index_json = index_json
        self.model_file_index = model_file_index
        self.open_parameter_index = open_parameter_index
        self.property = property

    def get_file_parameters(self):
        file_json = self.index_json["files"][self.model_file_index]
        if "file-parameter-values" in file_json:
            return file_json["file-parameter-values"]
        return []

    def get_open_parameters(self):
        file_json = self.index_json["files"][self.model_file_index]
        if "open-parameter-values" in file_json:
            open_par_json = file_json["open-parameter-values"]
            if len(open_par_json) > 0 and "values" in open_par_json[self.open_parameter_index]:
                return open_par_json[self.open_parameter_index]["values"]
        return []

    def get_parameters(self):
        result = []
        unsorted_parameters = self.get_file_parameters() + self.get_open_parameters()
        for p in self.index_json["parameters"]:
            pname = p["name"]
            for other_p in unsorted_parameters:
                if other_p["name"] == pname:
                    result.append(other_p)
                    break
        return result

    def get_open_parameter_def_string(self):
        """ Returns the definition of the open model parameters in the form 'N=2,K=5,p=0.3'.
        The returned string is empty if there are no parameters. """
        par_def_string = ""
        pars = self.get_open_parameters()
        for p in pars:
            if len(par_def_string) > 0:
                par_def_string = par_def_string + ","
            value_str = str(p["value"]).lower() if type(p["value"]) is bool else str(p["value"])
            par_def_string = par_def_string + "{}={}".format(p["name"], value_str)
        return par_def_string

    def get_parameter_values_string(self):
        par_val_string = ""
        pars = self.get_parameters()
        for p in pars:
            if len(par_val_string) > 0:
                par_val_string = par_val_string + "-"
            value_str = str(p["value"]).lower() if type(p["value"]) is bool else str(p["value"])
            par_val_string = par_val_string + value_str
        return par_val_string

    def get_model_short_name(self):
        return self.index_json["short"]

    def get_identifier(self):
        if self.property is None:
            return "{}.{}".format(self.get_model_short_name(), self.get_parameter_values_string())
        else:
            return "{}.property{}.{}".format(self.get_model_short_name(), self.property, self.get_parameter_values_string())

    def get_model_type(self):
        return self.index_json["type"]

    def is_ctmc(self):
        return self.get_model_type() == "ctmc"

    def is_dtmc(self):
        return self.get_model_type() == "dtmc"

    def is_mdp(self):
        return self.get_model_type() == "mdp"

    def is_ma(self):
        return self.get_model_type() == "ma"

    def is_pta(self):
        return self.get_model_type() == "pta"

    def get_original_format(self):
        return self.index_json["original"]

    def is_prism(self):
        return self.get_original_format() == "PRISM"

    def is_prism_inf(self):
        return self.get_original_format() == "PRISM-∞"

    def get_directory(self):
        return os.path.join(self.settings.benchmark_dir(), "{}/{}".format(self.get_model_type(), self.get_model_short_name()))

    def get_original_filename(self):
        result = self.index_json["files"][self.model_file_index]["original-file"]
        if isinstance(result, str):
            result = [result]
        return result

    def get_all_filenames(self):
        list = self.get_original_filename()
        if "converted-file" in self.index_json["files"][self.model_file_index]:
            list.append(self.index_json["files"][self.model_file_index]["converted-file"])
        return list

    def get_jani_filename(self):
        for f in self.get_all_filenames():
            if os.path.splitext(f)[1].lower() in [".jani"]:
                return f
        raise AssertionError("Unable to find jani program file.")

    def get_prism_filename(self):
        if not (self.is_prism()):
            raise AssertionError("Invalid operation: Not a prism model.")
        for f in self.get_all_filenames():
            if os.path.splitext(f)[1].lower() in [".prism", ".nm", ".pm", ".sm", ".ma"]:
                return f
        raise AssertionError("Unable to find prism program file.")


    def get_evt_category(self):
        if "evt-category" in self.index_json:
            return self.index_json["evt-category"]
        return "unknown"

    def get_stationary_category(self):
        if "stationary-category" in self.index_json:
            return self.index_json["stationary-category"]
        return "unknown"


    def load_jani_file(self):
        """ Returns the contens of the jani file """
        try:
            return load_json(os.path.join(self.get_directory(), self.get_jani_filename()))
        except UnicodeDecodeError:
            print("ERROR: Unable to load jani file '{}'".format(os.path.join(self.get_directory(), self.get_jani_filename())))
        return OrderedDict()

    def get_jani_features(self):
        """ Returns the list of jani features """
        model_jani = self.load_jani_file()
        if "features" in model_jani:
            return model_jani["features"]
        return []


def get_benchmark_from_id(settings, id):
    """ Returns the benchmark object associated with the given identifier """
    short_name = id.split(".")[0]
    id = "" if id == short_name else id[len(short_name)+1:]

    # find the correct benchmark
    benchmark_directories = load_json(os.path.join(settings.benchmark_dir(), "index.json"))
    model_index_json = None
    for p in benchmark_directories:
        model_path = os.path.join(settings.benchmark_dir(), p["path"])
        # get the correct index.json file
        if short_name == os.path.basename(model_path):
            model_index_json = load_json(os.path.join(model_path, "index.json"))
            break
    if model_index_json is None: raise LookupError("Unable to find benchmark with name '{}'.".format(short_name))

    # get the property
    property_str = None
    if "properties" in model_index_json and id.startswith("property"):
        id = id[len("property"):]
        for prop in model_index_json["properties"]:
            if id.startswith(prop + "."):
                property_str = prop
                id = id[len(prop)+1:]
                break
        if property_str is None: raise  LookupError("Unable to find property with name '{}'.".format(id))

    # get the parameter_definition as a map
    parameter_definition_str = id.strip()
    parameter_definition = OrderedDict()
    if parameter_definition_str != "":
        for p,v in zip(model_index_json["parameters"], parameter_definition_str.split("-")):
            parameter_definition[p["name"]] = v.strip()

    # find the file parameter_definition
    for model_file_index in range(len(model_index_json["files"])):
        file_info = model_index_json["files"][model_file_index]
        correct_file = True
        file_param_values = []
        if "file-parameter-values" in file_info:
            file_param_values = file_info["file-parameter-values"]
        for par_val in file_param_values:
            value_str = str(par_val["value"]).lower() if type(par_val["value"]) is bool else str(par_val["value"])
            if str(parameter_definition[par_val["name"]]) != value_str:
                correct_file = False
                break
        if correct_file:
            # find the open parameter values
            open_param_values = []
            if "open-parameter-values" in file_info:
                open_param_values = file_info["open-parameter-values"]
            if len(open_param_values) == 0:
                return Benchmark(settings, model_index_json, model_file_index, 0, property_str)
            for open_parameter_index in range(len(open_param_values)):
                correct_open_pars = True
                if "values" in open_param_values[open_parameter_index]:
                    for par_val in open_param_values[open_parameter_index]["values"]:
                        value_str = str(par_val["value"]).lower() if type(par_val["value"]) is bool else str(par_val["value"])
                        if str(parameter_definition[par_val["name"]]) != value_str:
                            correct_open_pars = False
                            break
                if correct_open_pars:
                    return Benchmark(settings, model_index_json, model_file_index, open_parameter_index, property_str)
    raise LookupError("Unable to find parameter definition '{}' for model '{}'.".format(parameter_definition, short_name))






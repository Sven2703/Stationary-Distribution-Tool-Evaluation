import itertools

from ..benchmark import Benchmark
from ..invocation import Invocation
from ..execution import *
from ..configuration import *
from ..solver import *


def get_name():
    """ return the name of the tool"""
    return "storm"

def get_default_executable():
   return "$ARTIFACT_DIR/bin/storm"

def get_export_format():
    """ return the format for exported results (--exportresults)"""
    return ".json"
def get_export_command(filename):
    return "--exportresult " + filename

def test_installation(settings, configuration = None):
    """
    Performs a quick check to test whether the installation works.
    Returns an error message if something went wrong and 'None' otherwise.
    """
    storm_executable = settings.tool_executable("storm")
    if not os.path.exists(set_artifact_dir(storm_executable)):
         return "Executable '{}' does not exist.".format(storm_executable)
    command_line = storm_executable + " {}".format("" if configuration is None else configuration.command)
    try:
        test_out, test_time, test_code = execute_command_line(command_line, 10)
        if test_code != 0:
            return "Error while executing:\n\t{}\nNon-zero return code: '{}'.".format(command_line, test_code)
    except KeyboardInterrupt:
        return "Error: Execution interrupted."
    except Exception:
        return "Error while executing\n\t{}\n".format(command_line)

    
    
def is_benchmark_supported(settings, benchmark : Benchmark):
    """ Auxiliary function that returns True if the provided benchmark is not supported by Storm and no known external conversion tool can help."""
    # Do not allow infinite state-spaces
    if benchmark.is_prism_inf():
        return False
    # Only allow DTMCs and CTMCs
    return benchmark.is_dtmc() or benchmark.is_ctmc()


def get_invocation(settings, benchmark : Benchmark, configuration : Configuration, solver : Solver, precision, export):
    """
    Returns an invocations that invokes the tool for the given benchmark and the given prism configuration.
    It can be assumed that the current directory is the directory from which execute_invocations.py is executed.
    If this benchmark is not supported, an empty list has to be returned.
    """
    general_arguments = "--timemem"  # Prints some timing and memory information

    invocation = Invocation()
    invocation.tool = get_name()
    invocation.configuration_id = configuration.identifier
    invocation.solver_id = solver.identifier
    invocation.note = configuration.note
    invocation.benchmark_id = benchmark.get_identifier()
    invocation.precision = precision
    invocation.export = export
    
    if is_benchmark_supported(settings, benchmark) and settings.task() in ['evts','stationary']:
        bdir = benchmark.get_directory()

        storm_executable = settings.tool_executable("storm") + " --statistics"
        if (benchmark.is_prism()):
            benchmark_arguments = "--prism {}".format(os.path.join(bdir, benchmark.get_prism_filename()))
            if benchmark.get_open_parameter_def_string() != "":
                benchmark_arguments += " --constants {}".format(benchmark.get_open_parameter_def_string())
            if benchmark.is_ctmc():
                benchmark_arguments += " --prismcompat"
                invocation.note += " Use `--prismcompat` to ensure compatibility with prism benchmark."
        else:
            # For, e.g., PGCL, GreatSPN benchmarks we use the .jani files
            janifile = benchmark.get_jani_filename()
            par_defs = benchmark.get_open_parameter_def_string()
            benchmark_arguments = "--jani {}".format(os.path.join(bdir, janifile))
            if par_defs != "":
                benchmark_arguments += " --constants " + par_defs

        if benchmark.property is not None:
            benchmark_arguments += " --prop {}".format(os.path.join(bdir, benchmark.property))

        # We do not set the precision for direct solvers such as "elimination" or "sparselu"
        if "exact" in solver.identifier:
            invocation.precision = "ignored"
        else:
            general_arguments += " --precision {}".format(float(precision))

        # export is set in execution as it depends on result dir

        task = "--expvisittimes" if settings.task() == "evts" else "--steadystate"
        invocation.set_command(storm_executable + " " + benchmark_arguments + " " + task + " " + solver.command + " " + configuration.command + " " + general_arguments)
    else:
        invocation.note += " Benchmark not supported by Storm."    
    return invocation



def check_execution(settings, execution : Execution):
    """
    Returns True if the execution was successful, i.e., if one can find the result in the tooloutput.
    This method is called after executing the commands of the associated invocation.
    """
    if settings.task() in ["stationary","evts"]:
        log = execution.concatenate_logs()
        pos = log.find("\nResult (")
        return pos >= 0
    else:
        raise Exception("Unsupported task {}.".format(settings.task()))


def is_not_supported(logfile):
    """
    Returns true if the logfile contains error messages that mean that the input is not supported.
    """
    # if one of the following error messages occurs, we are sure that the model is not supported.
    known_messages = []
    known_messages.append("The model type Markov Automaton is not supported by the hybrid engine.")
    known_messages.append("The model type Markov Automaton is not supported by the dd engine.")
    known_messages.append("The model type CTMC is not supported by the dd engine.")
    known_messages.append(
        "Cannot build symbolic model from JANI model whose system composition that refers to the automaton ")
    known_messages.append(
        "Cannot build symbolic model from JANI model whose system composition refers to the automaton ")
    known_messages.append("The symbolic JANI model builder currently does not support assignment levels.")
    for m in known_messages:
        if m in logfile:
            return True

    pos_message = logfile.find("Inspections (defined in line ")
    if pos_message >= 0:
        end_of_line = logfile.find("\n", pos_message)
        if logfile[:end_of_line].endswith(") are not supported."): return True

    # The following only indicates unsupported if there is no other error message before
    pos_message = logfile.find("Property is unsupported by selected engine/settings.")
    if pos_message >= 0:
        end_of_line_before = logfile[:pos_message].rfind("\n")
        if "ERROR" not in logfile[:end_of_line_before]:
            start_of_line_before = logfile[:end_of_line_before].rfind("\n") + 1
            line_before = logfile[start_of_line_before:end_of_line_before]
            if line_before.startswith("Model checking property"): return True

    return False


def is_memout(logfile):
    """
    Returns true if the logfile indicates an out of memory situation.
    Assumes that a result could not be parsed successfully.
    """
    known_messages = []
    known_messages.append("Maximum memory exceeded.")
    known_messages.append("BDD Unique table full")
    for m in known_messages:
        if m in logfile:
            return True
    # if there is no error message and no result is produced, we assume out of memory.
    return "ERROR" not in logfile


def get_configurations(task):
    default = Configuration(id="sparse", note="Sparse (default) engine",
                            command="--engine sparse")
    return [default]

def get_solvers(task):
    if task == "evts":

        solving_method = OrderedDict()
        solving_method["luexact"] = ["eigen --eigen:method sparselu --exact", "Using Eigen SparseLU and exact rational numbers (direct, precision ignored)."]
        solving_method["lu"] = ["eigen --eigen:method sparselu", "Using Eigen SparseLU (direct, precision ignored)."]
        solving_method["vi"] = ["native --native:method power", "Using value iteration (numerical)."]
        solving_method["gmres"] = ["gmm++ --gmm++:method gmres", "Using gmm++ GMRES (numerical)."]
        solving_method["ii"] = ["native --native:method ii --sound", "Using interval iteration (numerical, sound)."]
        solving_method["ovi"] = ["native --native:method ovi --sound", "Using optimistic value iteration (numerical, sound)."]

        approaches = OrderedDict()
        approaches[""] = ["", ""] # standard approach without topological solving
        approaches["-topo"] = ["topological --topological:eqsolver ", " Topological approach."]

        result = []
        for method,approach in itertools.product(solving_method, approaches):
            result.append(Solver(id="{}{}".format(method, approach),
                             note="{}{}".format(solving_method[method][1], approaches[approach][1]),
                             command="--eqsolver {}{}".format( approaches[approach][0], solving_method[method][0])))
        return result

    elif task == "stationary":
        eq_systems = OrderedDict()
        eq_systems["classic"] = ["classic", "Reachability and BSCCs solved via standard equation system."]
        eq_systems["evtreach"] = ["eqsys", "Reachability solved via EVTs, BSCCs solved via standard equation system."]
        eq_systems["evtfull"] = ["evt", "Reachability and BSCCs solved via EVTs."]

        solving_method = OrderedDict()
        solving_method["luexact"] = ["eigen --eigen:method sparselu --exact", "Using Eigen SparseLU and exact rational numbers (direct, precision ignored)."]
        solving_method["lu"] = ["eigen --eigen:method sparselu", "Using Eigen SparseLU (direct, precision ignored)."]
        solving_method["gmres"] = ["gmm++ --gmm++:method gmres", "Using gmm++ GMRES (numerical)."]
        solving_method["ii"] = ["native --native:method ii --sound", "Using interval iteration (numerical, sound)."]
        solving_method["ovi"] = ["native --native:method ovi --sound", "Using optimistic value iteration (numerical, sound)."]

        approaches = OrderedDict()
        # approaches[""] = ["", ""] # standard approach without topological solving, not considered in experiments
        approaches["-topo"] = ["topological --topological:eqsolver ", "Topological approach."]

        result = []
        for method,system,approach in itertools.product(solving_method, eq_systems, approaches):
            if method in ["ii", "ovi"] and system != "evtfull": continue # sound methods only for evtfull
            result.append(Solver(id="{}-{}{}".format(system, method, approach),
                                 note="{} {} {}".format(eq_systems[system][1], solving_method[method][1], approaches[approach][1]),
                                 command="{} --eqsolver {}{}".format(eq_systems[system][0], approaches[approach][0], solving_method[method][0])))
        return result

    else:
        raise AssertionError("Unsupported task {}.".format(task))


def get_mc_time(execution : Execution):
    """
    Returns the model checking (not wallclock-time) of the given execution on the given benchmark.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be a decimal number (time in seconds)
    """
    log = execution.concatenate_logs()

    pos = log.find("Time for model checking: ")
    if pos < 0:
        return None
    pos = pos + len("Time for model checking: ")
    eol_pos = log.find("s.\n", pos)
    mc_time = log[pos:eol_pos]

    return mc_time

def get_topology(execution : Execution):
    """
    Returns the topology of the model: cyclic (size of non-bottom SCC is >1) / acyclic (all non-bottom SCCs are of
    size one). This method is called after executing the commands of the associated invocation. One can either find
    the result in the tooloutput (as done here) or read the result from a file that the tool has produced. The
    returned value should be a string
    """
    log = execution.concatenate_logs()

    pos = log.find("# Topology of the input model without BSCCs (acyclic = only non-bottom SCCs of size 1): ")
    if pos < 0:
        return None
    pos = pos + len("# Topology of the input model without BSCCs (acyclic = only non-bottom SCCs of size 1): ")
    eol_pos = log.find("\n", pos)
    topology = log[pos:eol_pos]

    return topology


def get_evts_topo_precision(execution : Execution):
    """
    Returns the precision used during the computation
    (this is interesting as the precision is sometimes adjusted for topological computations).
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be a string
    """
    log = execution.concatenate_logs()

    pos = log.find("Precision for computation: ")
    if pos < 0:
        return None
    pos = pos + len("Precision for computation: ")
    eol_pos = log.find(" (", pos)
    precision = log[pos:eol_pos]

    return precision


def get_num_states(execution : Execution):
    """
    Returns the number of states of the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("States: 	")
    if pos < 0:
        return None
    pos = pos + len("States: 	")
    eol_pos = log.find("\n", pos)
    num_states = log[pos:eol_pos]

    return num_states

def get_num_trans_states(execution : Execution):
    """
    Returns the number of transient states of the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("# Number of non-BSCC states: ")
    if pos < 0:
        return None
    pos = pos + len("# Number of non-BSCC states: ")
    eol_pos = log.find("\n", pos)
    num_trans_states = log[pos:eol_pos]

    return num_trans_states


def get_num_sccs(execution : Execution):
    """
    Returns the number of non-bottom SCCs in the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("# Number of non-bottom SCCs: ")
    if pos < 0:
        return None
    pos = pos + len("# Number of non-bottom SCCs: ")
    eol_pos = log.find("\n", pos)
    num_sccs = log[pos:eol_pos]

    return num_sccs

def get_num_bsccs(execution : Execution):
    """
    Returns the number of BSCCs in the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("# Number of BSCCs: ")
    if pos < 0:
        return None
    pos = pos + len("# Number of BSCCs: ")
    eol_pos = log.find("\n", pos)
    num_bsccs = log[pos:eol_pos]

    return num_bsccs

def get_max_scc_size(execution : Execution):
    """
    Returns the maximal number of states in a non-bottom SCC of the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("# Size of largest non-bottom SCC: ")
    if pos < 0:
        return None
    pos = pos + len("# Size of largest non-bottom SCC: ")
    eol_pos = log.find(" states\n", pos)
    max_scc_size = log[pos:eol_pos]

    return max_scc_size

def get_max_bscc_size(execution: Execution):
    """
    Returns the maximal number of states in a BSCC of the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("# Size of largest BSCC: ")
    if pos < 0:
        return None
    pos = pos + len("# Size of largest BSCC: ")
    eol_pos = log.find(" states\n", pos)
    max_scc_size = log[pos:eol_pos]

    return max_scc_size

def get_max_scc_chain_length(execution : Execution):
    """
    Returns the maximal scc chain length of the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("# Length of max SCC chain: ")
    if pos < 0:
        return None
    pos = pos + len("# Length of max SCC chain: ")
    eol_pos = log.find("\n", pos)
    max_scc_chain_length = log[pos:eol_pos]

    return max_scc_chain_length



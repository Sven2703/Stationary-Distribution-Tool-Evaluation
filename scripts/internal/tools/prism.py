from ..benchmark import Benchmark
from ..invocation import Invocation
from ..execution import *
from ..configuration import *
from ..solver import *

def get_name():
    """ return the name of the tool"""
    return "prism"

def get_default_executable():
   return "$ARTIFACT_DIR/bin/prism"

def get_export_format():
    """
    Return the format for exported results (--exportresults).
    Export of results is not supported: return None
    """
    # print("Prism results can not be exported.")
    return ".txt"

def get_export_command(filename):
    """
       Return the command for exporting results.
       Export of results is not supported: return None
       """
    return "--exportss " + filename

def test_installation(settings, configuration=None):
    """
    Performs a quick check to test whether the installation works.
    Returns an error message if something went wrong and 'None' otherwise.
    """
    prism_executable = settings.tool_executable("prism")
    if not os.path.exists(set_artifact_dir(prism_executable)):
        return "Executable '{}' does not exist.".format(prism_executable)
    command_line = prism_executable + " {}".format("" if configuration is None else configuration.command)
    try:
        test_out, test_time, test_code = execute_command_line(command_line, 10)
        if test_code != 0:
            return "Error while executing:\n\t{}\nNon-zero return code: '{}'.".format(command_line, test_code)
    except KeyboardInterrupt:
        return "Error: Execution interrupted."
    except Exception:
        return "Error while executing\n\t{}\n".format(command_line)


def is_benchmark_supported(settings, benchmark: Benchmark):
    """ Auxiliary function that returns True if the provided benchmark is not supported by Prism and no known external conversion tool can help."""
    # DO not allow infinite state-spaces
    if benchmark.is_prism_inf() or (not benchmark.is_prism()):
        return False

    # Only allow DTMCs and CTMCs
    return benchmark.is_dtmc() or benchmark.is_ctmc()


def get_invocation(settings, benchmark: Benchmark, configuration: Configuration, solver: Solver, precision, export):
    """
    Returns an invocations that invokes the tool for the given benchmark and the given prism configuration.
    It can be assumed that the current directory is the directory from which execute_invocations.py is executed.
    If this benchmark is not supported, an empty list has to be returned.
    """


    invocation = Invocation()
    invocation.tool = get_name()
    invocation.configuration_id = configuration.identifier
    invocation.solver_id = solver.identifier
    invocation.note = configuration.note
    invocation.benchmark_id = benchmark.get_identifier()
    invocation.precision = precision
    invocation.export = export

    if is_benchmark_supported(settings, benchmark) and settings.task() in ['stationary']:
        bdir = benchmark.get_directory()

        prism_executable = settings.tool_executable("prism")

        benchmark_arguments = str(os.path.join(bdir, benchmark.get_prism_filename()))
        if benchmark.get_open_parameter_def_string() != "":
            benchmark_arguments += " -const {}".format(benchmark.get_open_parameter_def_string())

        general_arguments = ""
        # We always set the precision. But not in exact mode (not supported yet)
        if ("-exact" in configuration.command):
            invocation.precision = "ignored"
        else:
            general_arguments += " -epsilon {}".format(float(precision))

        # export command is added in execution

        invocation.set_command(
            prism_executable + " " + benchmark_arguments + " -steadystate " + solver.command + " " + configuration.command + " " + general_arguments)
    else:
        invocation.note += " Benchmark or file format not supported by Prism."
    return invocation

def check_execution(settings, execution : Execution):
    """
    Returns True if the execution was successful, i.e., if one can find the result in the tooloutput.
    This method is called after executing the commands of the associated invocation.
    """
    if settings.task() in ["stationary"]:
        log = execution.concatenate_logs()
        pos = log.find("Result: ")
        if pos >= 0:
            return True
        pos = log.find("Printing steady-state probabilities in plain text format below:")
        return pos >= 0
    else:
        raise Exception("Unsupported task {}.".format(settings.task()))


def is_not_supported(logfile):
    """
    Returns true if the logfile contains error messages that mean that the input is not supported.
    """
    # if one of the following error messages occurs, we are sure that the model is not supported.
    known_messages = []
    known_messages.append("Error: Syntax error (")
    known_messages.append("Cannot read the input file ")
    known_messages.append(" not supported")
    known_messages.append("Invalid (or unsupported) ")
    known_messages.append("Unsupported operator in label expression: ")
    known_messages.append("unsupported model type: ")
    known_messages.append("Unsupported type for constant ")
    known_messages.append("Unsupported expression ")
    for m in known_messages:
        if m in logfile:
            return True

    return False


def is_memout(logfile):
    """
    Returns true if the logfile indicates an out of memory situation.
    Assumes that a result could not be parsed successfully.
    """
    known_messages = []
    known_messages.append("java.lang.OutOfMemory")
    known_messages.append("java.lang.StackOverflowError")
    for m in known_messages:
        if m in logfile:
            return True
    return False
    # if there is no error message and no result is produced, we assume out of memory
    # return "error" not in logfile and "ERROR" not in logfile

def get_configurations(task):
    # default = Configuration(id="default", note="Default engine.",command="")
    # hybrid_abs = Configuration(id="hybrid-abs", note="Hybrid (default) engine and absolute error criterion ",
    #                            command="-hybrid -absolute")
    # hybrid_rel = Configuration(id="hybrid-rel",
    #                            note="Hybrid (default) engine and relative error criterion",
    #                            command="-hybrid -relative")
    # sparse_abs = Configuration(id="sparse-abs",
    #                            note="Sparse engine and absolute error criterion",
    #                            command="-sparse -absolute")
    # sparse_rel = Configuration(id="sparse-rel", note="Sparse engine and relative error criterion ",
    #                            command="-sparse -relative")
    # explicit_abs = Configuration(id="explicit-abs",
    #                              note="Explicit engine and absolute error criterion",
    #                              command="-explicit -absolute")
    explicit_rel = Configuration(id="explicit-rel", note="Explicit engine and relative error criterion ",
                                 command="-explicit -relative")
    return [explicit_rel]
    # return [explicit_rel, hybrid_rel, sparse_rel]

def get_solvers(task):
    default = Solver(id="default", note="Numerical solving method: (Default)", command="")
    # power = Solver(id="power", note="Numerical solving method: Power method", command="--power")
    # jacobi = Solver(id="jacobi", note="Numerical solving method: Jacobi (default)", command="--jacobi")
    # gaussseidel = Solver(id="gaussseidel", note="Numerical solving method: Jacobi", command="--gaussseidel")
    # sor = Solver(id="sor", note="Numerical solving method: SOR, default-over-relaxation: 0.9", command="--sor")
    # jor = Solver(id="jor", note="Numerical solving method: JOR, default-over-relaxation: 0.9", command="--jor")
    return [default]



def get_mc_time(execution: Execution):
    """
    Returns the model checking (not wallclock-time) of the given execution on the given benchmark.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be a decimal number (time in seconds)
    """
    log = execution.concatenate_logs()

    pos = log.find("Time for steady-state probability computation: ")
    if pos < 0:
        return None
    pos = pos + len("Time for steady-state probability computation: ")
    eol_pos = log.find(" seconds.\n", pos)
    mc_time = log[pos:eol_pos]

    return mc_time

def get_num_states(execution: Execution):
    """
    Returns the number of states of the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("States:      ")
    if pos < 0:
        return None
    pos = pos + len("States:      ")
    eol_pos = log.find(" (", pos)
    num_states = log[pos:eol_pos]

    return num_states


def get_num_trans_states(execution: Execution):
    """
    Returns the number of transient states of the model.
    This method is called after executing the commands of the associated invocation.
    One can either find the result in the tooloutput (as done here) or
    read the result from a file that the tool has produced.
    The returned value should be an integer
    """
    log = execution.concatenate_logs()

    pos = log.find("non-BSCC states: ")
    if pos < 0:
        return None
    pos = pos + len("non-BSCC states: ")
    eol_pos = log.find("\n", pos)
    num_trans_states = log[pos:eol_pos]

    return num_trans_states

def get_num_sccs(execution: Execution):
    """
    Not supported.
    """
    return None

def get_num_bsccs(execution : Execution):
    """
    NA
    """
    return None

def get_topology(execution : Execution):
    """
    NA
    """
    return None

def get_max_scc_chain_length(execution : Execution):
    """
    NA
    """
    return None

def get_max_scc_size(execution: Execution):
    """
    Not available in Prism output
    """
    return None

def get_max_bscc_size(execution: Execution):
    """
    Not available in Prism output
    """
    return None


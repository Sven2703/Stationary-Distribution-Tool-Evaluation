from ..benchmark import Benchmark
from ..invocation import Invocation
from ..execution import *
from ..configuration import *
from ..solver import *


def get_name():
    """ return the name of the tool"""
    return "sds"

def get_default_executable():
   return "$ARTIFACT_DIR/bin/sds"

def get_export_format():
    """
    Return the format for exported results (--exportresults).
    Export of results is not supported: return None
    """

    # print("sds results can not be exported.")
    return None

def get_export_command(filename):
    """
       Return the command for exporting results.
       Export of results is not supported: return None
       """
    return None

def test_installation(settings, configuration=None):
    """
    Performs a quick check to test whether the installation works.
    Returns an error message if something went wrong and 'None' otherwise.
    """
    sds_executable = settings.tool_executable("sds")
    if not os.path.exists(set_artifact_dir(sds_executable)):
        return "Executable '{}' does not exist.".format(sds_executable)
    command_line = sds_executable + " {}".format("--version")
    try:
        test_out, test_time, test_code = execute_command_line(command_line, 10)
        if test_code != 0:
            return "Error while executing:\n\t{}\nNon-zero return code: '{}'.".format(command_line, test_code)
    except KeyboardInterrupt:
        return "Error: Execution interrupted."
    except Exception:
        return "Error while executing\n\t{}\n".format(command_line)


def is_benchmark_supported(settings, benchmark: Benchmark):
    """ Auxiliary function that returns True if the provided benchmark is not supported by the tool and no known external conversion tool can help."""
    # Do not allow infinite state-spaces and non-prism models
    if benchmark.is_prism_inf() or (not benchmark.is_prism()):
        return False
    # Only allow DTMCs, CTMCs and MDPs
    return benchmark.is_dtmc() or benchmark.is_ctmc() or benchmark.is_mdp()


def get_invocation(settings, benchmark: Benchmark, configuration: Configuration, solver: Solver, precision, export):
    """
    Returns an invocations that invokes the tool for the given benchmark and the given configuration.
    It can be assumed that the current directory is the directory from which execute_invocations.py is executed.
    For QCOMP 2019, this should return a list of size at most two, where
    the first entry (if present) corresponds to the default configuration of the tool and
    the second entry (if present) corresponds to an optimized setting (e.g., the fastest engine and/or solution technique for this benchmark).
    Please only provide two invocations if there is actually a difference between them.
    If this benchmark is not supported, an empty list has to be returned.
    For testing purposes, the script also allows to return more than two invocations.
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

        sds_executable = settings.tool_executable("sds")
        benchmark_arguments = os.path.join(bdir, benchmark.get_prism_filename())
        if benchmark.get_open_parameter_def_string() != "":
            benchmark_arguments += " --const {}".format(benchmark.get_open_parameter_def_string())

        # We always set the precision.
        general_arguments = " --precision {}".format(float(precision))
        invocation.set_command(sds_executable + " " + benchmark_arguments + " " + configuration.command + " " + solver.command + " " +general_arguments)

    else:
        invocation.note += " Benchmark not supported by SDS."
    return invocation

def check_execution(settings, execution : Execution):
    """
    Returns True if the execution was successful, i.e., if one can find the result in the tooloutput.
    This method is called after executing the commands of the associated invocation.
    """
    if settings.task() in ["stationary"]:
        log = execution.concatenate_logs()
        pos = log.find("Bounds: ")

        if pos >= 0:
            return True
        pos = log.find("solve")
        pos = log.find("(", pos)
        if pos >= 0:
            return True
    else:
        raise Exception("Error for task '{}' using SDS.".format(settings.task()))


def is_memout(logfile):
    """
    Returns true if the logfile indicates an out of memory situation.
    Assumes that a result could not be parsed successfully.
    """
    known_messages = []
    known_messages.append("NegativeArraySizeException")
    known_messages.append("ArrayIndexOutOfBounds")
    known_messages.append("java.lang.StackOverflowError")
    known_messages.append("java.lang.OutOfMemoryError")
    for m in known_messages:
        if m in logfile:
            return True
    return False

def get_configurations(task):
    default = Configuration(id="default-abs",
                            note="default engine and absolute (default) error criterion ",
                            command="")
    return [default]

def get_solvers(task):
    naive = Solver(id="ap-naive", note="Approximate, naive sampling (approximate --sampling SAMPLE_NAIVE)",
                   command="approximate --sampling SAMPLE_NAIVE")
    sample = Solver(id="ap-sample", note="Approximate, target sampling (approximate --sampling SAMPLE_TARGET)",
                    command="approximate --sampling SAMPLE_TARGET")

    return [naive, sample]


def get_mc_time(execution: Execution):
    """
    NA
    """
    return None

def get_num_states(execution: Execution):
    """
    NA
    """
    return None


def get_num_trans_states(execution: Execution):
    """
    NA
    """
    return None


def get_num_sccs(execution: Execution):
    """
    NA
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
    NA
    """
    return None

def get_max_bscc_size(execution: Execution):
    """
    NA
    """
    return None


def is_not_supported(logfile):
    """
    Returns true if the logfile contains error messages that mean that the input is not supported.
    """
    # if one of the following error messages occurs, we are sure that the model is not supported.
    known_messages = []
    known_messages.append("IllegalArgumentException")
    for m in known_messages:
        if m in logfile:
            return True
    return False



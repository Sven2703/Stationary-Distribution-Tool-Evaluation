from ..benchmark import Benchmark
from ..invocation import Invocation
from ..execution import *
from ..configuration import *
from ..solver import *


def get_name():
    """ return the name of the tool"""
    return "greatspn"

def get_default_executable():
   return "$ARTIFACT_DIR/bin/greatspn.sh"

def get_export_format():
    """
    Return the format for exported results (--exportresults).
    Export of results is not supported: return None
    """
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
    greatspn_executable = settings.tool_executable("greatspn")
    if not os.path.exists(set_artifact_dir(greatspn_executable)):
        return "GreatSPN script '{}' does not exist.".format(greatspn_executable)

def is_benchmark_supported(settings, benchmark: Benchmark):
    """ Auxiliary function that returns False if the provided benchmark is not supported by the tool and no known external conversion tool can help."""
    # Only allow greatspn models
    if benchmark.get_original_format().lower() != "greatspn": return False
    if len( benchmark.get_original_filename()) == 0: return False
    return benchmark.get_original_filename()[0].lower().endswith(".pnpro")

def get_invocation(settings, benchmark: Benchmark, configuration: Configuration, solver: Solver, precision, export):
    """
    Returns an invocations that invokes the tool for the given benchmark and the given configuration.
    It can be assumed that the current directory is the directory from which execute_invocations.py is executed.
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

        great_executable = settings.tool_executable("greatspn")

        benchmark_arguments = os.path.join(bdir, benchmark.get_original_filename()[0][:-len(".pnpro")])

        # assemble output dir
        output_dir = os.path.join(settings.results_dir_exports(), "greatspnoutput", invocation.get_identifier())

        # We always set the precision.
        general_arguments = "{}".format(float(precision))
        invocation.set_command(great_executable + " " + benchmark_arguments + " " + output_dir + " " + general_arguments)

    else:
        invocation.note += " Benchmark not supported by GreatSPN."
    return invocation

def check_execution(settings, execution : Execution):
    """
    Returns True if the execution was successful, i.e., if one can find the result in the tooloutput.
    This method is called after executing the commands of the associated invocation.
    """
    if settings.task() in ["stationary"]:
        log = execution.concatenate_logs()
        return "Showing results for all places:" in log
    else:
        raise Exception("Error for task '{}' using GreatSPN.".format(settings.task()))


def is_memout(logfile):
    """
    Returns true if the logfile indicates an out of memory situation.
    Assumes that a result could not be parsed successfully.
    """
    known_messages = []
    for m in known_messages:
        if m in logfile:
            return True
    return False

def get_configurations(task):
    default = Configuration(id="default",
                            note="Build reachability graph explicitly ",
                            command="")
    return [default]

def get_solvers(task):
    ggsc = Solver(id="ggsc", note="GreatSPN Steady State solver)",
                   command="")

    return [ggsc]


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
    for m in known_messages:
        if m in logfile:
            return True
    return False


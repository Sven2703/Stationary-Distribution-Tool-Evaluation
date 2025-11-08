import argparse
from internal.benchmark import *
from internal.invocation import *
from internal.settings import *
from internal.tools import greatspn, sds, storm, prism

import traceback


def create_invocations(settings, benchmark_selection):
    invocations = []

    # input time limit for all invocations
    """ Asks the user to enter a time limit."""
    time_limit = 1800
    while True:
        response = input(
            "Enter a time limit (in seconds) after which executions are aborted [{}]: ".format(time_limit))
        if response == "": break
        if is_number(response):
            time_limit = int(response)
            break
        else:
            print("Time limit should be a number.")

    # loading benchmarks for all invocations
    benchmarks_csv = load_csv(benchmark_selection)
    benchmarks = OrderedDict([("dtmc", []), ("ctmc", [])])
    for benchmark_csv in benchmarks_csv:
        if len(benchmark_csv) > 4:
            benchmark_id = "{}.property{}.{}".format(benchmark_csv[0], benchmark_csv[4], benchmark_csv[3])
        elif len(benchmark_csv) == 4:
            benchmark_id = "{}.{}".format(benchmark_csv[0], benchmark_csv[3])
        else:
            benchmark_id = "{}".format(benchmark_csv[0])
        benchmark = get_benchmark_from_id(settings, benchmark_id)
        benchmarks[benchmark.get_model_type()].append(benchmark)
    print("Loaded {} benchmarks from selection '{}'".format(len(benchmarks_csv), benchmark_selection))
    # model type selection
    model_types = OrderedDict()
    model_types["dtmc"] = ["Discrete Time Markov Chains", "({} benchmarks)".format(len(benchmarks["dtmc"]))]
    model_types["ctmc"] = ["Continuous Time Markov Chains", "({} benchmarks)".format(len(benchmarks["ctmc"]))]
    selected_model_types = command_line_input("models", model_types)
    # filter benchmarks by model
    selected_benchmarks = []
    for model_type in selected_model_types:
        for benchmark in benchmarks[model_type]:
            selected_benchmarks.append(benchmark)


    # tool selection
    tools = OrderedDict()
    tools["storm"] = "Storm: https://www.stormchecker.org"
    if settings.task() == "stationary":
        # model checkers that do not support EVTs computation:
        tools["prism"] = "Prism: http://www.prismmodelchecker.org"
        tools["sds"] = "SDS  tool: https://github.com/incaseoftrouble/stationary-distribution-sampling"
        tools["greatspn"] = "GreatSPN: https://github.com/greatspn/SOURCES"

    stop_creating_invocs = False
    while not stop_creating_invocs:

        """ Asks the user to select a tool."""
        toolstring = "".join('\n  - {} ({})'.format(k, v) for k, v in tools.items())
        while True:
            response = input("Choose a tool from {}: ".format(toolstring)).lower()
            if response == "":
                continue
            elif response == "storm":
                tool = storm
                break
            elif response == "prism":
                tool = prism
                break
            elif response == "sds":
                tool = sds
                break
            elif response == "greatspn":
                tool = greatspn
                break
            else:
                print(("The tool '{}' is not available .").format(response))


        # Get and test directory of tool binary
        settings.input_tool_executable(tool.get_name())
        test_result = tool.test_installation(settings)
        if test_result is not None:
            input("Press Return to continue or CTRL+C to abort.")


        """ Asks the user to select solvers."""
        # Get and test tools' solvers
        existing_solvers = tool.get_solvers(task)
        selected_solver_identifiers = command_line_input("solvers", OrderedDict(
            [(solver.identifier, [solver.note, solver.command]) for solver in existing_solvers]))
        selected_solvers = []
        for solver in existing_solvers:
            if solver.identifier in selected_solver_identifiers:
                selected_solvers.append(solver)
        print("Selected {} solving methods.".format(len(selected_solvers)))

        """ Asks the user to select configurations."""
        existing_configurations = tool.get_configurations(tool)
        for config in existing_configurations:
            # test configuration
            test_result = tool.test_installation(settings, config)
            if test_result is not None:
                print("Error when testing configuration '{}':".format(config.identifier))
                print(test_result)
                input("Press Return to continue or CTRL+C to abort.")
        selected_config_identifiers = command_line_input("configurations", OrderedDict(
            [(config.identifier, [config.note, config.command]) for config in existing_configurations]))
        selected_configurations = []
        for config in existing_configurations:
            if config.identifier in selected_config_identifiers:
                selected_configurations.append(config)
        print("Selected {} configurations.".format(len(selected_configurations)))



        # precision input
        """ Asks the user to enter the precision(s)."""
        precisions=set()
        while True:
            response = input(
                "Enter the precision which is used for iterative methods. "
                "\nThe precision is ignored for all direct solving methods. "
                "\nPossible inputs are: '0.001', '0.0001', ... ")
            if is_number(response) and float(response) > 0:
                precisions.add(float(response))
                response = input("Choose more precisions (type 'y' or 'n'): ")
                if response == "y":
                    continue
                elif response == "n":
                    break
            else:
                print("Precision should be a number >0.")

        num_invocations = len(selected_benchmarks) * len(selected_configurations) * len(selected_solvers) * len(precisions)
        print("Selected {} benchmarks, {} configurations {} solving methods and {} precisions yielding {} invocations in total.".format(len(selected_benchmarks), len(selected_configurations), len(selected_solvers),len(precisions), num_invocations))


        """ Asks the user if .json files containing the EVTs/stationary distributions should be exported."""

        if tool.get_export_format is not None:
            while True:
                response = input("Should files containing the " + ("EVTs" if str(task) == "evts" else "stationary probabilities") + " be created (y/n).")
                if response == "y":
                    export = True
                    break
                if response == "n":
                    export = False
                    break
        else:
            export = False
            print("Export of files containing the " + ("EVTs" if str(task) == "evts" else "stationary probabilities is not available for {}.").format(tool.get_name()))


        # creating invocations
        progressbar = Progressbar(num_invocations, "Generating invocations")
        i = 0
        unsupported = []
        for benchmark in selected_benchmarks:
            for configuration in selected_configurations:
                for solver in selected_solvers:
                    for precision in precisions:
                        i += 1
                        progressbar.print_progress(i)
                        invocation = tool.get_invocation(settings, benchmark, configuration, solver, precision, export)
                        if invocation.command == "":
                            unsupported.append(invocation.get_identifier() + ": " + invocation.note)
                        else:
                            invocation.time_limit = time_limit
                            invocations.append(invocation)

        print("")
        if len(unsupported) > 0:
            print("{} invocations are not supported:".format(len(unsupported)))
            for inv in unsupported:
                print("\t" + inv)

        while True:
            response = input("Generate more invocations with a different tool selection (type 'y' or 'n'): ")
            if response == "n":
                stop_creating_invocs = True
                break
            if response == "y":
                stop_creating_invocs = False
                break

    return invocations


def check_invocations(settings, invocations):

    invocation_number = 0
    if len(invocations) > 1:
        progressbar = Progressbar(len(invocations), "Checking invocations")
    else:
        sys.stdout.write("Checking invocation ... ")
        sys.stdout.flush()
    invocation_identifiers = set()
    for invocation in invocations:
        invocation_number = invocation_number + 1
        if len(invocations) > 1:
            progressbar.print_progress(invocation_number)
        try:
            # check whether there is no command
            if invocation.command == "":
                continue
            benchmark = get_benchmark_from_id(settings, invocation.benchmark_id)
            # ensure that the actual benchmark files exist
            for filename in benchmark.get_all_filenames():
                if not os.path.isfile(set_artifact_dir(os.path.join(benchmark.get_directory(), filename))):
                    raise AssertionError(
                        "The file '{}' does not exist.".format(os.path.join(benchmark.get_directory(), filename)))
            # ensure that the invocation identifier (consisting of benchmark and configuration id) can be a filename and are unique
            if not is_valid_filename(invocation.get_identifier(), "/"):
                raise AssertionError(
                    "Invocation identifier '{}' is either not a valid filename or contains a '.'.".format(
                        invocation.get_identifier()))
            if invocation.get_identifier() in invocation_identifiers:
                raise AssertionError("Invocation identifier '{}' already exists.".format(invocation.get_identifier()))
            invocation_identifiers.add(invocation.get_identifier())
        except Exception:
            print("Error when checking invocation #{}: {}".format(invocation_number - 1, invocation.get_identifier()))
            traceback.print_exc()
    print("")


def run_invocations(settings, invocations):
    invocation_number = 0
    if len(invocations) > 1:
        progressbar = Progressbar(len(invocations), "Executing invocations")
    else:
        sys.stdout.write("Executing invocation ... ")
        sys.stdout.flush()
    try:
        for invocation in invocations:
            if invocation.tool == "storm":
                tool = storm
            elif invocation.tool == "prism":
                tool = prism
            elif invocation.tool == "sds":
                tool = sds
            elif invocation.tool == "greatspn":
                tool = greatspn
            else:
                raise AssertionError("Tool '{}' is not allowed.".format(invocation.tool))

            invocation_number = invocation_number + 1
            if len(invocations) > 1:
                progressbar.print_progress(invocation_number)
            # execute the invocation
            notes = []

            if invocation.export == True and tool.get_export_format() is not None:
                # we do not want to change the command in .json file, only for this execution
                export_value_file = os.path.join(settings.results_dir_exports(), invocation.get_identifier()) + tool.get_export_format()
                invocation.command = invocation.command + " " + tool.get_export_command(export_value_file)
                invocation.export_value_file = export_value_file

            execution = invocation.execute()
            tool_result = execution.to_json()
            try:
                success = tool.check_execution(settings, execution)
            except Exception as e:
                print("ERROR while getting result for invocation #{}: {}".format(invocation_number - 1,
                                                                                 invocation.get_identifier()))
                # traceback.print_exc()
            # if the execution was successful, we save the mc-time
            if success:
                mc_time = tool.get_mc_time(execution)
                if mc_time is not None:
                    tool_result["mc-time"] = str(mc_time)
                    # wallclock-time was already set in execution
            elif not execution.timeout and not execution.error:
                notes.append("Unable to obtain tool result.")
                tool_result["execution-error"] = True
            tool_result["notes"] = notes
            logfile_name = invocation.get_identifier() + ".log"
            tool_result["log"] = logfile_name

            if invocation.export == True:
                if tool.get_export_format() is not None:
                    # export is set and tool supports export
                    if os.path.isfile(set_artifact_dir(invocation.export_value_file)):
                        tool_result["export-value-file"] = invocation.export_value_file
                    else: notes.append(("Export file {} does not exist.").format(invocation.export_value_file))
                else: notes.append("Tool does not support file export.")

            # save --statistic data
            num_states = tool.get_num_states(execution)
            if num_states is not None:
                tool_result["states"] = int(num_states)

            num_trans_states = tool.get_num_trans_states(execution)
            if num_trans_states is not None:
                tool_result["transient-states"] = str(num_trans_states)

            num_sccs = tool.get_num_sccs(execution)
            if num_sccs is not None:
                tool_result["non-bottom-SCCs"] = str(num_sccs)

            num_bsccs = tool.get_num_bsccs(execution)
            if num_bsccs is not None:
                tool_result["bottom-SCCs"] = str(num_bsccs)

            max_scc_size = tool.get_max_scc_size(execution)
            if max_scc_size is not None:
                tool_result["max-non-bottom-SCC-size"] = str(max_scc_size)

            max_bscc_size = tool.get_max_bscc_size(execution)
            if max_bscc_size is not None:
                tool_result["max-bottom-SCC-size"] = str(max_bscc_size)

            topology = tool.get_topology(execution)
            if topology is not None:
                tool_result["topology"] = str(topology)

            max_scc_chain_length = tool.get_max_scc_chain_length(execution)
            if max_scc_chain_length is not None:
                tool_result["max-SCC-chain-length"] = str(max_scc_chain_length)

            # save logfile
            path=set_artifact_dir(os.path.join(settings.results_dir_logs(), logfile_name))
            with open(path, 'w', encoding="utf-8") as logfile:
                logfile.write(execution.concatenate_logs())
                if len(notes) > 0:
                    logfile.write("\n" + "#" * 30 + " Notes " + "#" * 30 + "\n")
                for note in notes:
                    logfile.write(note + "\n")
            # save tool results in json format
            save_json(tool_result, os.path.join(settings.results_dir_logs(), invocation.get_identifier() + ".json"))
    except KeyboardInterrupt as e:
        print("\nInterrupt while processing invocation #{}: {}".format(invocation_number - 1,
                                                                       invocation.get_identifier()))
    except Exception:
        print("ERROR while processing invocation #{}: {}".format(invocation_number - 1, invocation.get_identifier()))
        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmarking tool. This script selects and executes benchmarks. "
                                                 "Usage: 'python3 run.py' Creates and executes a set of (new) invocations.")

    parser.add_argument('-t', '--task',
                        help="Choose a task from 'evts' and 'stationary'."
                             "Usage: 'python3 run.py' -t <task>'.", required=True)

    parser.add_argument('-r', '--results_dir',
                        help='The result directory. Usage: -r path/to/result/... ',
                        required=True)



    # Allow -b only if -f not set and vice versa
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-b', '--benchmarks',
                        help="A .csv containing the benchmark set. ", required=False)

    group.add_argument('-f', '--file',
                       help="Executes benchmarks from a previously created invocations file located at <filename>.  "
                            "Omit to create a new set of invocations."
                            "Usage: '-f <filename>'. ", required=False)
    parser.add_argument('-i', '--invocation', help="Only has an effect if the invocation file is set via [-f, --file]. "
                                                   "Executes the <n>th invocation (0 based) from a previously created invocations file located at <filename>."
                                                   "Usage: '-f <filename>' -i <n>", required=False)


    args = parser.parse_args()
    task = str(args.task)
    if task not in ["evts", "stationary"]:
        raise AssertionError("The task argument has to be set to 'evts' or 'stationary'.")

    settings = Settings(task, args.results_dir)
    settings.ensure_result_dirs()

    if args.file is None:

        benchmark_selection = args.benchmarks
        if not os.path.isfile(set_artifact_dir(args.benchmarks)):
            raise AssertionError("Benchmark selection file {} does not exist".format(benchmark_selection))

        input(("No invocations file loaded. Loaded benchmark selection file: '{}'. \nPress Return to create one now or CTRL+C to abort.").format(benchmark_selection))


        while True:
            response = input("\033[1;32m Enter a filename to store the invocations for later usage or press Return to continue: \033[0m")
            if response == "":
                break
            if is_valid_filename(set_artifact_dir(response)):
                if os.path.isfile(set_artifact_dir(response)):
                    if input("File {} exists.\033[1;31m Overwrite? \033[0m (type 'y' or 'n'): ".format(response)) != "y":
                        continue
                invocation_filename = response
                break
            else:
                print("Invalid file name {}".format(response))

        invocations = create_invocations(settings, benchmark_selection)
        invocations_json = [inv.to_json() for inv in invocations]
        if response != "":
            save_json(invocations_json, response)
            print("Saved {} invocations to file '{}'.".format(len(invocations), response))
            print("To load these invocations at a later time, you may run\n\tpython3 {} {}".format(sys.argv[0], response))

    else:
        # invocations file exists
        if not os.path.isfile(set_artifact_dir(args.file)):
            raise AssertionError("Invocations file {} does not exist".format(args.file))
        invocations_json = load_json(args.file)
        invocations = [Invocation(inv) for inv in invocations_json]
        print("Loaded {} invocations.".format(len(invocations)))
        if args.invocation is not None:
            if not is_number(args.invocation): raise AssertionError(
                "Expected a number for second argument but got '{}' instead.".format(args.invocation))
            selected_index = int(args.invocation)
            if selected_index not in range(0, len(invocations)): raise AssertionError(
                "Second argument is out of range: got '{}' but index has to be at least 0 at less than {}".format(
                    selected_index, len(invocations)))
            invocations = [invocations[selected_index]]
            print("Selected invocation #{}: {}".format(selected_index, invocations[0].get_identifier()))

    check_invocations(settings, invocations)
    run_invocations(settings, invocations)

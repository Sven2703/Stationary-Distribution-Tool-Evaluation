import argparse
from internal.export import *
from internal.settings import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Storm benchmarking tool. "
                                                 "This script gathers data of executions and exports them in various ways. "
                                                 "Usage: 'python3 postrocess.py'")
    parser.add_argument('-t', '--task',
                        help="Choose a task from 'evts' and 'stationary'."
                             "Usage: 'python3 run.py' -t <task>'.", required=True)
    parser.add_argument('-c', '--compare',
                        help='Use this flag enable the comparison of the EVT results. The location of the files can be specified using using the --logs argument.',
                        action='store_true')
    parser.add_argument('-r', '--results_dir',
                        help='The result directories.  '
                             'Usage: -r <path/to/result> ', required=True)
    parser.add_argument('-l', '--time_limit',
                        help='The maximum value for runtime.  '
                             'Usage: -l <number> ', required=True)

    args = parser.parse_args()

    task = str(args.task)
    if task not in ["evts", "stationary"]:
        raise AssertionError("The task argument has to be set to 'EVTs' or 'stationary'.")
    time_limit = float(args.time_limit)

    settings = Settings(task, args.results_dir)
    settings.test_result_dirs()



    # Gather execution data
    exec_data = OrderedDict()  # Tool -> Config -> Solver -> Benchmark -> Data

    benchmark_ids = []
    tools_configs_solvers_precisions = OrderedDict()  # Tool x Config x Solver x precision -> Num Supported
    logdir = settings.results_dir_logs()
    print("Log-Directory: " + str(logdir))
    if not os.path.isdir(logdir):
        print("Error: Directory '{}' does not exist.".format(logdir))

   

    for res_json in [load_json(os.path.join(logdir, f)) for f in os.listdir(logdir) if
                     f.endswith(".json") and os.path.isfile(set_artifact_dir(os.path.join(logdir, f)))]:
        tool = res_json["tool"]
        config = res_json["configuration-id"]
        solver = res_json["solver-id"]
        precision = res_json["precision"]
        benchmark = res_json["benchmark-id"]

        exec_data.setdefault(tool, OrderedDict())
        exec_data[tool].setdefault(config, OrderedDict())
        exec_data[tool][config].setdefault(solver, OrderedDict())
        exec_data[tool][config][solver].setdefault(precision, OrderedDict())

        if benchmark in exec_data[tool][config][solver][precision]:
            print("Error: Multiple result files found for {}.{}.{}.{}.{}".format(tool, config, solver, precision,
                                                                                 benchmark))
        res_json["log"] = os.path.join(logdir, res_json["log"])
        exec_data[tool][config][solver][precision][benchmark] = res_json
        if not benchmark in benchmark_ids:
            benchmark_ids.append(benchmark)
        tools_configs_solvers_precisions.setdefault((tool, config, solver, precision), 0)
        if not is_not_supported(res_json):
            tools_configs_solvers_precisions[(tool, config, solver, precision)] += 1

    benchmark_ids.sort()
    print("Found Data for {} benchmarks and {} tool-config-solver-precision combinations".format(len(benchmark_ids),
                                                                                                 len(tools_configs_solvers_precisions)))
    print("Number of supported benchmarks (of {}):".format(len(benchmark_ids)))
    for (t, c, s, p) in tools_configs_solvers_precisions:
        print("{}.{}.{}.{}: {}".format(t, c, s, p, tools_configs_solvers_precisions[(t, c, s, p)]))

    tools_configs_solvers_precision_sorted = []

    for (t, c, s, p) in tools_configs_solvers_precisions:
        if (t, c, s, p) not in tools_configs_solvers_precision_sorted:
            tools_configs_solvers_precision_sorted.append((t, c, s, p))

    additional_info_keys = ["states"]
    print("Gather the following additional benchmark info: {}".format(additional_info_keys))

    benchmark_infos = gather_benchmark_info(exec_data, additional_info_keys, benchmark_ids,
                                            tools_configs_solvers_precisions)

    print("Comparison of runtimes...")

    if task not in ["evts", 'stationary']:
        raise AssertionError("Unsupported task {}.".format(settings.task()))

    # runtime including model building time
    value_key = "wallclock-time"
    print("Generating file {} and {} for runtime scatter plots".format(
        os.path.join(settings.results_dir_logs(), value_key + "-scatter.csv"),
        os.path.join(settings.results_dir_logs(), value_key + "-texpgf-scatter.csv")))
    generate_scatter_tex_csv(settings, exec_data, additional_info_keys, benchmark_infos,
                             tools_configs_solvers_precision_sorted,
                             settings.results_dir_plots(), value_key, MIN_VALUE_local=1, MAX_VALUE_local=time_limit,
                             TO_VALUE_local=6000, NA_VALUE_local=6000)
    print("Generating file {} for quantile plots".format(
        os.path.join(settings.results_dir_plots(), value_key + "-quantile.csv")))
    generate_quantile_csv(settings, exec_data, benchmark_ids, tools_configs_solvers_precision_sorted,
                          settings.results_dir_plots(), value_key, MIN_VALUE_local=1, MAX_VALUE_local=time_limit, only_prism=(task=="stationary"))
    print("Generating interactive html tables for runtimes in directory {}".format(settings.results_dir_tables()))
    generate_table(settings, exec_data, additional_info_keys, benchmark_infos, tools_configs_solvers_precision_sorted,
                   settings.results_dir_tables(), value_key, overwrite_logs=True)


    print("-" * 30 + "\nSummary of results:\n")
    print(generate_summary_table(settings, exec_data, benchmark_ids, tools_configs_solvers_precision_sorted))



    if args.compare:
        if settings.task() == "stationary": print("WARN: Prism and sds export is not implemented.")
        # If comparison is turned on, we collect the baseline data
        # i.e., exact computations and direct solving methods:
        tools_configs_solvers_precision_baseline_sorted = []
        # The baseline values are gathered from direct solving methods, with exact computations:
        for (t, c, s, p) in tools_configs_solvers_precisions:
            if t.lower() == "storm" and "luexact" in s:
                tools_configs_solvers_precision_baseline_sorted.append((t, c, s, p))


        print("Comparison of results...")
        print("Baseline via: " + str(tools_configs_solvers_precision_baseline_sorted))
        # get the max norm and mean derivation wrt absolute and relative error. Result saved in key
        # "relative/absolute-error-max-norm-value" and "relative/absolute-error-mean_deviation_value"
        exec_data = generate_comparison_values(exec_data, benchmark_ids,
                                               tools_configs_solvers_precision_baseline_sorted,
                                               tools_configs_solvers_precision_sorted)

        print("Generating interactive html table for result comparison (wrt absolute and relative error) in directory {}".format(
                settings.results_dir_tables()))

        # save interactive html tables: dont overwrite the table log files: they have already been created during runtime comparison
        value_key = "relative-error-max-norm-value"
        generate_table(settings, exec_data, additional_info_keys, benchmark_infos,
                       tools_configs_solvers_precision_sorted, settings.results_dir_tables(), value_key,
                       overwrite_logs=False)
        print("Generating file {} and {} for error scatter plots".format(
            os.path.join(settings.results_dir_logs(), value_key + "-scatter.csv"),
            os.path.join(settings.results_dir_logs(), value_key + "-texpgf-scatter.csv")))
        # cut values >=1
        generate_scatter_tex_csv(settings, exec_data, additional_info_keys, benchmark_infos,
                                 tools_configs_solvers_precision_sorted,
                                 settings.results_dir_plots(), value_key, MIN_VALUE_local=0.0000001, MAX_VALUE_local=1,
                                 TO_VALUE_local=5, NA_VALUE_local=-15)

        # runtime including model building
        inc_difference = "relative-error-max-norm-value"
        value_key = "wallclock-time"
        print(
            "Generating file {} for runtime scatter plots, marking incorrect results (w.r.t. relative-error-max-norm-value).".format(
                os.path.join(settings.results_dir_logs(), value_key + "-INC-" + inc_difference + "-texpgf-scatter.csv")))
        # cut values >=time_limit
        generate_scatter_tex_csv(settings, exec_data, additional_info_keys, benchmark_infos,
                                 tools_configs_solvers_precision_sorted,
                                 settings.results_dir_plots(), value_key, MIN_VALUE_local=1, MAX_VALUE_local=time_limit,
                                 TO_VALUE_local=6000, NA_VALUE_local=6000, INC_VALUE_local=6000,
                                 incorrect_filter=(inc_difference, 0.001))

        print(
            "Generating file {} for quantile plots. Incorrect results are considered unsolved (w.r.t. relative-error-max-norm-value).".format(
                os.path.join(settings.results_dir_plots(), value_key + "-INC-" + inc_difference + "-quantile.csv")))
        # cut values >=time_limit
        generate_quantile_csv(settings, exec_data, benchmark_ids, tools_configs_solvers_precision_sorted,
                              settings.results_dir_plots(), value_key, MIN_VALUE_local=1, MAX_VALUE_local=time_limit,
                              incorrect_filter=(inc_difference, 0.001), only_prism=(task=="stationary"))


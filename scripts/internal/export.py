from .benchmark import *
from .tools import prism, storm, sds, greatspn
from collections import Counter
import numpy as np
import ijson  # reading large jsons

INC_VALUE = -1000 # incorrect result
MO_VALUE = -3000  # Out of memory
TO_VALUE = -3000  # timeout
NA_VALUE = -8000  # not available
NS_VALUE = -8000  # not supported
ERR_VALUE = -8000  # Unknown error
NB_VALUE = -10000  # no baseline  (has to be smaller than everything else)

# helper function for saving additional information - keys of benchmark_info ("topology", "bottom-SCCs" etc.).
def gather_benchmark_info(exec_data, additional_info_keys, benchmark_ids, tools_configs_solvers_precision):
    benchmark_infos = {}
    for benchmark_id in benchmark_ids:
        additional_info_values = [NA_VALUE for key in additional_info_keys]
        benchmark_info = dict(zip(additional_info_keys, additional_info_values))

        completed_benchmark_info_number = 0
        for (t, c, s, p) in tools_configs_solvers_precision:

            if completed_benchmark_info_number == len(additional_info_keys):
                # we have gathered the complete benchmark info
                break

            elif benchmark_id in exec_data[t][c][s][p]:
                # we have not gathered the complete benchmark info yet, try to find it in the next json
                res_json = exec_data[t][c][s][p][benchmark_id]
                for key in additional_info_keys:
                    if benchmark_info[key] == NA_VALUE and (key in res_json) and ("ERROR" not in str(res_json[key])):
                        benchmark_info[key] = str(res_json[key])
                        completed_benchmark_info_number += 1

        benchmark_infos[benchmark_id] = benchmark_info
    return benchmark_infos


# Reads an execution result in json format and detects if it indicates an error due to not supporting the benchmark
def is_not_supported(result_json):
    if "execution-error" not in result_json or result_json["execution-error"] == False:
        return False
    path = set_artifact_dir(result_json["log"])
    with open(path, 'r') as logfile:
        if "storm" in result_json["tool"].lower():
            return storm.is_not_supported(logfile.read())
        elif "prism" in result_json["tool"].lower():
            return prism.is_not_supported(logfile.read())
        elif "sds" in result_json["tool"].lower():
            return sds.is_not_supported(logfile.read())
        elif "greatspn" in result_json["tool"].lower():
            return greatspn.is_not_supported(logfile.read())
    return False


# Reads an execution result in json format and detects if it indicates a memory error
def is_memout(result_json):
    if "execution-error" not in result_json or result_json["execution-error"] == False:
        return False
    path = set_artifact_dir(result_json["log"])
    with open(path, 'r') as logfile:
        if "storm" in result_json["tool"].lower():
            return storm.is_memout(logfile.read())
        elif "prism" in result_json["tool"].lower():
            return prism.is_memout(logfile.read())
        elif "sds" in result_json["tool"].lower():
            return sds.is_memout(logfile.read())
        elif "greatspn" in result_json["tool"].lower():
            return greatspn.is_memout(logfile.read())
    return False


# Generates a csv containing runtimes. A row corresponds to a benchmark, a column corresponds to a tool/config combination.
# The first three columns contain the benchmark id, the model type, and the original format
# The last column contains the lowest runtime of the corresponding rows.
# .._VALUE_local can be varied for easier latex formatting
def generate_scatter_tex_csv(settings, exec_data, additional_info_keys, benchmark_infos, tools_configs_solvers_precisions,
                             output_dir, value_key, MIN_VALUE_local, MAX_VALUE_local, TO_VALUE_local, NA_VALUE_local, INC_VALUE_local = None, incorrect_filter = None):

    result = [
        ["Benchmark-id","Name","Parameters","Type", "Orig", "evt-category", "stationary-category"] + additional_info_keys + ["{}.{}.{}.{}".format(t, c, s, p) for (t, c, s, p) in
                                                           tools_configs_solvers_precisions] + ["Best"]]
    for benchmark_id, value in benchmark_infos.items():
        benchmark = get_benchmark_from_id(settings, benchmark_id)
        benchmark_info = benchmark_infos[benchmark_id]
        row = [benchmark_id, benchmark.get_model_short_name(), benchmark.get_parameter_values_string(), benchmark.get_model_type().lower(), benchmark.get_original_format().lower(), benchmark.get_evt_category().lower(), benchmark.get_stationary_category().lower()]
        for key in additional_info_keys:
            row.append(benchmark_info[key])

        best_value = NA_VALUE_local
        for (tool, config, solver, precision) in tools_configs_solvers_precisions:
            value = NA_VALUE_local
            if benchmark_id in exec_data[tool][config][solver][precision]:
                res_json = exec_data[tool][config][solver][precision][benchmark_id]
                if value_key in res_json and res_json[value_key] == NB_VALUE:
                    value = NB_VALUE
                elif incorrect_filter is not None and incorrect_filter[0] in res_json and res_json[incorrect_filter[0]] != NB_VALUE and res_json[incorrect_filter[0]] != NA_VALUE and res_json[incorrect_filter[0]] > incorrect_filter[1]:
                    value = INC_VALUE_local
                elif "timeout" in res_json and res_json["timeout"] == True:
                    value = TO_VALUE_local
                elif value_key in res_json and float(res_json[value_key]) > MAX_VALUE_local:
                    value = MAX_VALUE_local
                elif "execution-error" in res_json and res_json["execution-error"] == True:
                    if is_memout(res_json):
                        value = TO_VALUE_local
                    elif is_not_supported(res_json):
                        value = NA_VALUE_local
                    else:
                        # print("Unexpected error for '{}.{}.{}.{}.{}'".format(tool, config, solver, precision, benchmark_id))
                        value = NA_VALUE_local
                elif value_key in res_json:
                    if float(res_json[value_key]) >= 0:
                        # if no error occurred, we determine the best value
                        value = max(MIN_VALUE_local, float(res_json[value_key]))
                        value = min(value, MAX_VALUE_local)
                        best_value = min(best_value, value) if best_value >= 0 else value
                    elif float(res_json[value_key]) == TO_VALUE or \
                            float(res_json[value_key]) == MO_VALUE:
                        value = TO_VALUE_local
                    else:
                        value = NA_VALUE_local
                else:
                    # print("Unexpected execution result for '{}.{}.{}.{}.{}'".format(tool, config, solver, precision, benchmark_id))
                    # value stays NA but positive
                    value = NA_VALUE_local
            row.append(str(value))
        row.append(str(best_value))
        result.append(row)

    save_csv(result, os.path.join(output_dir, value_key + ("-INC-"+incorrect_filter[0] if incorrect_filter is not None else "") + "-texpgf-scatter.csv"))


# Generates a csv containing runtimes. The first column denotes the row indices. Each of the remaining column corresponds to a tool/config combination.
# The last column corresponds to the fastest (smallest value) tool/config
# An entry in the ith row corresponds to the runtime/(value) of the ith fastest/(smallest value) benchmark
def generate_quantile_csv(settings, exec_data, benchmark_ids, tools_configs_solvers_precisions, output_dir, value_key,
                          MIN_VALUE_local,MAX_VALUE_local, incorrect_filter=None, only_prism=False):
    values_best_dict = OrderedDict()
    for (t, c, s, p) in tools_configs_solvers_precisions:
        values_best_dict[t] = OrderedDict()
    result = [["n"] + ["{}.{}.{}.{}shifted".format(t, c, s, p) for (t, c, s, p) in tools_configs_solvers_precisions] + [
        "{}.bestshifted".format(tool) for tool in
        values_best_dict]]  # append 'shifted' for compatibility with qcomp latex
    values = OrderedDict()

    not_prism = []

    for (tool, config, solver, precision) in tools_configs_solvers_precisions:
        values_tc = []
        for benchmark_id in benchmark_ids:

            benchmark = get_benchmark_from_id(settings, benchmark_id)
            if only_prism and not benchmark.is_prism():
                # we skip non-prism benchmarks, because jani is not supported by each tool
                if benchmark_id not in not_prism:
                    not_prism.append(benchmark_id)
                continue

            if benchmark_id in exec_data[tool][config][solver][precision]:
                res_json = exec_data[tool][config][solver][precision][benchmark_id]
                if incorrect_filter is not None and incorrect_filter[0] in res_json and res_json[incorrect_filter[0]] != NB_VALUE and res_json[incorrect_filter[0]] != NA_VALUE and res_json[incorrect_filter[0]] > incorrect_filter[1]:
                    # incorrect_filter[0] is not in res_json for tool = prism / sds
                    # incorrect result
                    continue
                if "timeout" in res_json and res_json["timeout"] == True:
                    # timeout
                    continue
                elif value_key in res_json and float(res_json[value_key]) > MAX_VALUE_local:
                    # exceeded time limit
                    continue
                if "execution-error" in res_json and res_json["execution-error"] == True:
                    # exec error
                    continue
                if value_key in res_json and res_json[value_key] != NB_VALUE:
                    # result exists
                    values_tc.append(max(MIN_VALUE_local, float(res_json[value_key])))
                    if benchmark_id not in values_best_dict[tool]:
                        values_best_dict[tool][benchmark_id] = values_tc[-1]
                    else:
                        values_best_dict[tool][benchmark_id] = min(values_best_dict[tool][benchmark_id],
                                                                   values_tc[-1])

        values_tc.sort()
        if len(values_tc) == 0:
            values_tc.append(MAX_VALUE_local *10) # Not available
        values["{}.{}.{}.{}".format(tool, config, solver, precision)] = values_tc
    for tool in values_best_dict:
        values_best = [values_best_dict[tool][b] for b in values_best_dict[tool]]
        values_best.sort()
        values["{}.best".format(tool)] = values_best
    for i in range(len(benchmark_ids)-len(not_prism)):
        row = [str(i + 1)]
        for tc in values:
            if i < len(values[tc]):
                row.append(str(values[tc][i]))
            else:
                row.append("")
        result.append(row)
    print("Correctly solved benchmarks (of {}):".format(len(benchmark_ids)-len(not_prism)))
    for tc in values:
        print("\t{}: {}".format(tc, len(values[tc])))

    save_csv(result, os.path.join(output_dir, value_key + ("-INC-"+incorrect_filter[0] if incorrect_filter is not None else "") + "-quantile.csv"))


def generate_summary_table(settings, exec_data, benchmark_ids, tools_configs_solvers_precision):
    solved = Counter()
    solved_fastest1 = Counter()
    solved_fastest2 = Counter()
    not_supported = Counter()
    timeout = Counter()
    memout = Counter()
    incorrect = Counter()
    error = Counter()
    for benchmark_id in benchmark_ids:
        benchmark = get_benchmark_from_id(settings, benchmark_id)
        best_value = NA_VALUE
        solving_times = dict()
        for (tool, config, solver, precision) in tools_configs_solvers_precision:
            if benchmark_id in exec_data[tool][config][solver][precision]:
                res_json = exec_data[tool][config][solver][precision][benchmark_id]
                if "timeout" in res_json and res_json["timeout"] == True:
                    timeout[(tool, config, solver, precision)] += 1
                elif "execution-error" in res_json and res_json["execution-error"] == True:
                    if is_memout(res_json):
                        memout[(tool, config, solver, precision)] += 1
                    elif is_not_supported(res_json):
                        not_supported[(tool, config, solver, precision)] += 1
                    else:
                        # print("Unexpected error for '{}.{}.{}.{}.{}'".format(tool, config, solver, precision, benchmark_id))
                        error[(tool, config, solver, precision)] += 1
                elif "timeout" in res_json and "mc-time" in res_json:
                    solved[(tool, config, solver, precision)] += 1
                    value = float(res_json["mc-time"])
                    solving_times[(tool, config, solver, precision)] = value
                    best_value = min(best_value, value) if best_value >= 0 else value
                # else:
                    # print("Unexpected execution result for '{}.{}.{}.{}.{}'".format(tool, config, solver, precision, benchmark_id))
            else:
                not_supported[(tool, config, solver, precision)] += 1
        # count fastest
        for tc in solving_times:
            if solving_times[tc] <= 1.01 * best_value:
                solved_fastest1[tc] += 1
            if solving_times[tc] <= 1.5 * best_value:
                solved_fastest2[tc] += 1
        solved["best"] += min(len(solving_times), 1)

    result = r"""\begin{tabular}{r|""" + "r" * len(tools_configs_solvers_precision) + """}""" + "\n"
    for (t, c, s, p) in tools_configs_solvers_precision:
        result += "\t& " + """\multicolumn{1}{c}{\engine{""" + c + "}}\n"
    result += "\\\\\\hline\n"
    result += """\#solved     &""" + "\t&".join([" {}".format(solved[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += """\#not supp.  &""" + "\t&".join(
        [" {}".format(not_supported[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += """\#time-outs  &""" + "\t&".join(
        [" {}".format(timeout[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += """\#mem-outs   &""" + "\t&".join([" {}".format(memout[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += """\#incorrect  &""" + "\t&".join(
        [" {}".format(incorrect[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += """\#error      &""" + "\t&".join([" {}".format(error[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += """\#fastest101 &""" + "\t&".join(
        [" {}".format(solved_fastest1[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += """\#fastest150 &""" + "\t&".join(
        [" {}".format(solved_fastest2[tc]) for tc in tools_configs_solvers_precision]) + "\\\\\n"
    result += r"""\end{tabular}""" + "\n"
    result += "% A total of {} instances could be solved.".format(solved["best"])
    return result


# Aux function for writing in files with proper indention
def write_line(file, indention, content):
    file.write("\t" * indention + content + "\n")


# Generates an html log page for the given result within output_dir/logs/
def create_log_page(settings, result_json, output_dir, overwrite_logs):
    b = get_benchmark_from_id(settings, result_json["benchmark-id"])
    if not "log" in result_json:
        raise AssertionError("Expected a log file.")
    path = set_artifact_dir(result_json["log"])
    with open(path, 'r') as logfile:
        logs = logfile.read().split("#" * 40)
    f_path = os.path.join("logs/", os.path.basename(result_json["log"])[:-4] + ".html")

    if not overwrite_logs:
        return f_path

    path = set_artifact_dir(os.path.join(output_dir, f_path))
    with open(path, 'w') as f:
        indention = 0
        write_line(f, indention, "<!DOCTYPE html>")
        write_line(f, indention, "<html>")
        write_line(f, indention, "<head>")
        indention += 1
        write_line(f, indention, '<meta charset="UTF-8">')
        write_line(f, indention,
                   "<title>{}.{}.{} - {} {}</title>".format(result_json["tool"], result_json["configuration-id"],
                                                            result_json["solver-id"], b.get_model_short_name(),
                                                            b.get_parameter_values_string()))
        # write_line(f, indention, '<link rel="stylesheet" type="text/css" href="{}">'.format("http://qcomp.org/style.css"))
        write_line(f, indention,
                   '<link rel="stylesheet" type="text/css" href=../style.css>')
        indention -= 1
        write_line(f, indention, '</head>')
        write_line(f, indention, '<body>')
        write_line(f, indention, '<h1>{}.{}.{}</h1>'.format(result_json["tool"], result_json["configuration-id"],
                                                            result_json["solver-id"]))

        write_line(f, indention, '<div class="box">')
        indention += 1
        write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Benchmark</div></div>')
        write_line(f, indention, '<table style="margin-bottom: 0.75ex;">')
        indention += 1
        # TODO: case qcomp model: add link
        # write_line(f, indention, '<tr><td>Model:</td><td><a href="{}">{}</a> <span class="tt">v.{}</span> ({})</td></tr>'.format("http://qcomp.org/benchmarks/index.html#{}".format(b.get_model_short_name()),b.get_model_short_name(), b.index_json["version"], b.get_model_type().upper()))
        write_line(f, indention, '<tr><td>Model:</td><td> ({})</td></tr>'.format(b.get_model_short_name(), b.get_model_type().upper()))  # TODO: replaced line above
        write_line(f, indention, '<tr><td>Parameter(s)</td><td>{}</td></tr>'.format(", ".join(['<span class="tt">{}</span> = {}'.format(p["name"], p["value"]) for p in b.get_parameters()])))
        indention -= 1
        write_line(f, indention, "</table>")
        indention -= 1
        write_line(f, indention, "</div>")

        write_line(f, indention, '<div class="box">')
        indention += 1
        write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Invocation ({}.{})</div></div>'.format(result_json["configuration-id"], result_json["solver-id"]))
        f.write('\t' * indention + '<pre style="overflow: auto; padding-bottom: 1.5ex; padding-top: 1ex; font-size: 15px; margin-bottom: 0ex;  margin-top: 0ex;">')
        command_str = str(result_json["command"])
        for filtered_path in settings.filtered_paths():
            command_str = command_str.replace(filtered_path, "")
        write_line(f, indention, command_str)
        f.write('</pre>\n')
        write_line(f, indention, result_json["invocation-note"])
        indention -= 1
        write_line(f, indention, "</div>")

        write_line(f, indention, '<div class="box">')
        indention += 1
        write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Execution</div></div>')
        write_line(f, indention, '<table style="margin-bottom: 0.75ex;">')
        indention += 1
        if result_json["timeout"]:
            write_line(f, indention,
                       '<tr><td>Walltime (MC-Time):</td><td style="color: red;">&gt {}s (NA) (Timeout)</td></tr>'.format(
                           result_json["time-limit"]))
        else:
            if "mc-time" in result_json:
                write_line(f, indention, '<tr><td>Walltime (MC-Time):</td><td style="tt">{}s ({}s)</td></tr>'.format(
                    result_json["wallclock-time"], result_json["mc-time"]))
            else:
                write_line(f, indention, '<tr><td>Walltime (MC-Time):</td><td style="tt">{}s (NA)</td></tr>'.format(
                    result_json["wallclock-time"]))

            return_codes = []
            if "return-codes" in result_json:
                return_codes = result_json["return-codes"]
            if result_json["execution-error"]:
                write_line(f, indention, '<tr><td>Return code:</td><td style="tt; color: red;">{}</td></tr>'.format(
                    ", ".join([str(rc) for rc in return_codes])))
            else:
                write_line(f, indention, '<tr><td>Return code:</td><td style="tt">{}</td></tr>'.format(
                    ", ".join([str(rc) for rc in return_codes])))
        first = True
        for note in result_json["notes"]:
            write_line(f, indention, '<tr><td>{}</td><td>{}</td></tr>'.format("Note(s):" if first else "", note))
            first = False
        if "relative-error" in result_json:
            write_line(f, indention, '<tr><td>Relative Error:</td><td style="tt{}">{}</td></tr>'.format(
                "" if result_json["result-correct"] else "; color: red", result_json["relative-error"]))
        indention -= 1
        write_line(f, indention, "</table>")
        indention -= 1
        write_line(f, indention, "</div>")

        for log in logs:
            for filtered_path in settings.filtered_paths():
                log = log.replace(filtered_path, "")
            pos = log.find("\n", log.find("Output:\n")) + 1
            pos_end = log.find("#############################", pos)
            if pos_end < 0:
                pos_end = len(log)
            log_str = log[pos:pos_end].strip()
            if len(log_str) != 0:
                write_line(f, indention, '<div class="box">')
                indention += 1
                write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Log</div></div>')
                f.write("\t" * indention + '<pre style="overflow:auto; padding-bottom: 1.5ex">')
                f.write(log_str)
                write_line(f, indention, '</pre>')
                indention -= 1
                write_line(f, indention, "</div>")

            pos = log.find("##############################Output to stderr##############################\n")
            if pos >= 0:
                pos = log.find("\n", pos) + 1
                write_line(f, indention, '<div class="box">')
                indention += 1
                write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">STDERR</div></div>')
                f.write("\t" * indention + '<pre style="overflow:auto; padding-bottom: 1.5ex">')
                pos_end = log.find("#############################", pos)
                if pos_end < 0:
                    pos_end = len(log)
                f.write(log[pos:pos_end].strip())
                write_line(f, indention, '</pre>')
                indention -= 1
                write_line(f, indention, "</div>")
        write_line(f, indention, "</body>")
        write_line(f, indention, "</html>")
    return f_path


# Generates an interactive html table from the results
def generate_table(settings, exec_data, additional_info_keys, benchmark_infos, tools_configs_solvers_precision, output_dir, value_key,
                   overwrite_logs=True):
    SHOW_UNSUPPORTED = True  # Also add entries for benchmarks that are known to be unsupported

    ensure_directory(output_dir)
    ensure_directory(os.path.join(output_dir, "logs/"))

    first_tool_col = 6 + len(additional_info_keys)
    num_cols = first_tool_col + len(tools_configs_solvers_precision)

    path = set_artifact_dir(os.path.join(output_dir, value_key + ".html"))
    with open(path, 'w') as tablefile:
        tablefile.write(r"""<!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Benchmark results</title>
      <link rel="stylesheet" type="text/css" href="style.css">
      <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.13/css/jquery.dataTables.min.css">
      <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/1.2.4/css/buttons.dataTables.min.css">
      <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/fixedheader/3.1.2/css/fixedHeader.dataTables.min.css">

      <script type="text/javascript" language="javascript" charset="utf8" src="https://code.jquery.com/jquery-1.12.4.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/1.10.13/js/jquery.dataTables.min.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/fixedheader/3.1.2/js/dataTables.fixedHeader.min.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/buttons/1.2.4/js/dataTables.buttons.min.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/buttons/1.2.4/js/buttons.colVis.min.js"></script>

      <script>
        $(document).ready(function() {
          // Set correct file
          $("#content").load("data.html");
        } );

        function updateBest(table) {
          // Remove old best ones
          table.cells().every( function() {
            $(this.node()).removeClass("best");
          });
          table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
              var bestValue = -1
              var bestIndex = -1
              $.each( this.data(), function( index, value ){
                if (index > 8 && table.column(index).visible()) {
    			    var text = $(value).text()
    	            if (["TO", "ERR", "INC", "MO", "NS", "NA", "NO BASELINE", ""].indexOf(text) < 0) {
    				    var number = parseFloat(text);
    	                if (bestValue == -1 || bestValue > number) {
    	                  // New best value
    	                  bestValue = number;
    	                  bestIndex = index;
    	                }
    				  }
    			  }
              });
              // Set new best
              if (bestIndex >= 0) {
                $(table.cell(rowIdx, bestIndex).node()).addClass("best");
              }
          } );
      }
      function updateWorst(table) {
          // Remove old worst ones
          table.cells().every( function() {
            $(this.node()).removeClass("worst");
          });
          table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
              var worstValue = -1
              var worstIndex = -1
              $.each( this.data(), function( index, value ){
                if (index > 8 && table.column(index).visible()) {
    			    var text = $(value).text()
    	            if (["TO", "ERR", "INC", "MO", "NS", "NA", "NO BASELINE", ""].indexOf(text) < 0) {
    				    var number = parseFloat(text);
    	                if (worstValue == -1 || worstValue < number) {
    	                  // New worst value
    	                  worstValue = number;
    	                  worstIndex = index;
    	                }
    				  }
    			  }
              });
              // Set new worst
              if (worstIndex >= 0) {
                $(table.cell(rowIdx, worstIndex).node()).addClass("worst");
              }
          } );
          }
      </script>
    </head>
    """)
        indention = 0
        write_line(tablefile, indention, "<body>")
        write_line(tablefile, indention, "<div>")
        indention += 1
        write_line(tablefile, indention, '<table id="table" class="display">')
        indention += 1
        write_line(tablefile, indention, '<thead>')
        indention += 1
        write_line(tablefile, indention, '<tr>')
        indention += 1
        benchmark_info_headers = additional_info_keys
        for head in ["Model", "Parameters", "Type", "Original", "EVT cat.", "Stationary cat."] + benchmark_info_headers + ["{}.{}.{}.{}".format(t, c, s, p)
                                                                                            for (t, c, s, p) in
                                                                                            tools_configs_solvers_precision]:
            write_line(tablefile, indention, '<th>{}</th>'.format(head))
        indention -= 1
        write_line(tablefile, indention, '</tr>')
        indention -= 1
        write_line(tablefile, indention, '</thead>')
        write_line(tablefile, indention, '<tbody>')
        indention += 1

        for benchmark_id, value in benchmark_infos.items():
            b = get_benchmark_from_id(settings, benchmark_id)
            write_line(tablefile, indention, '<tr>')
            indention += 1
            # TODO in case qcomp model:
            #  write_line(tablefile, indention, '<td><a href="{}">{}</a></td>'.format("http://qcomp.org/benchmarks/index.html#{}".format(b.get_model_short_name()), b.get_model_short_name()))
            write_line(tablefile, indention, '<td>{}</td>'.format(b.get_model_short_name()))  # TODO replaced line above
            write_line(tablefile, indention, '<td>{}</td>'.format(b.get_model_type().upper()))
            write_line(tablefile, indention, '<td>{}</td>'.format(b.get_parameter_values_string()))
            write_line(tablefile, indention, '<td>{}</td>'.format(b.get_original_format()))
            write_line(tablefile, indention, '<td>{}</td>'.format(b.get_evt_category()))
            write_line(tablefile, indention, '<td>{}</td>'.format(b.get_stationary_category()))

            # Fill the cells containing info about the model's topology and the precison used for the computation
            benchmark_info = benchmark_infos[benchmark_id]
            cell_contents = ""
            for key, value in benchmark_info.items():
                cell_contents += '<td>{}</td>'.format(value)
            write_line(tablefile, indention, cell_contents)

            for (t, c, s, p) in tools_configs_solvers_precision:
                cell_content = ""  # for mc-runtime
                if benchmark_id in exec_data[t][c][s][p]:
                    res_json = exec_data[t][c][s][p][benchmark_id]
                    link_attributes = ""
                    if "timeout" in res_json and res_json["timeout"] is True:
                        res_str = "TO"
                        link_attributes = " class='timeout'"
                    elif "execution-error" in res_json and res_json["execution-error"] is True:
                        if is_memout(res_json):
                            res_str = "MO"
                            link_attributes = " class='memout'"
                        elif is_not_supported(res_json):
                            res_str = "NS" if SHOW_UNSUPPORTED else None
                            link_attributes = " class='unsupported'"
                        else:
                            res_str = "ERR"
                            link_attributes = " class='error'"
                            # print("Unexpected error for '{}.{}.{}.{}.{}' (found while creating table)".format(t, c, s, p,benchmark_id))
                    elif value_key in res_json and (res_json[value_key] == NB_VALUE):
                        res_str = "NO BASELINE"
                        link_attributes = " class='nobaseline'"
                    elif "timeout" in res_json and "execution-error" in res_json and value_key in res_json:
                        res_str = res_json[value_key]
                    else:
                        res_str = "NA"
                        link_attributes = " class='notavailable'"
                        # print("Unexpected execution result for '{}.{}.{}.{}.{}'".format(t, c, s, p, benchmark_id))
                    if res_str is not None:
                        logpage = create_log_page(settings, res_json, output_dir, overwrite_logs)
                        cell_content = "<a href='{}' {}>{}</a>".format(logpage, link_attributes, res_str)
                write_line(tablefile, indention, '<td>{}</td>'.format(cell_content))
            indention -= 1
            write_line(tablefile, indention, '</tr>')
        indention -= 1
        write_line(tablefile, indention, '</tbody>')
        indention -= 1
        indention -= 1
        write_line(tablefile, indention, '</table>')
        write_line(tablefile, indention, "<script>")
        indention += 1
        write_line(tablefile, indention, 'var table = $("#table").DataTable( {')
        indention += 1
        write_line(tablefile, indention, '"paging": false,')
        write_line(tablefile, indention, '"autoWidth": false,')
        write_line(tablefile, indention, '"info": false,')
        write_line(tablefile, indention, 'fixedHeader: {')
        indention += 1
        write_line(tablefile, indention, '"header": true,')
        indention -= 1
        write_line(tablefile, indention, '},')
        write_line(tablefile, indention, '"dom": "Bfrtip",')
        write_line(tablefile, indention, 'buttons: [')
        indention += 1
        for columnIndex in range(first_tool_col, num_cols):
            write_line(tablefile, indention, '{')
            indention += 1
            write_line(tablefile, indention, 'extend: "columnsToggle",')
            write_line(tablefile, indention, 'columns: [{}],'.format(columnIndex))
            indention -= 1
            write_line(tablefile, indention, "},")
        tool_columns = [i for i in range(first_tool_col, num_cols)]
        for text, show, hide in zip(["Show all", "Hide all"], [tool_columns, []], [[], tool_columns]):
            write_line(tablefile, indention, '{')
            indention += 1
            write_line(tablefile, indention, 'extend: "colvisGroup",')
            write_line(tablefile, indention, 'text: "{}",'.format(text))
            write_line(tablefile, indention, 'show: {},'.format(show))
            write_line(tablefile, indention, 'hide: {}'.format(hide))
            indention -= 1
            write_line(tablefile, indention, "},")
        indention -= 1
        write_line(tablefile, indention, "],")
        indention -= 1
        write_line(tablefile, indention, "});")
        indention -= 1
        write_line(tablefile, indention, "")
        indention += 1
        write_line(tablefile, indention, 'table.on("column-sizing.dt", function (e, settings) {')
        indention += 1
        write_line(tablefile, indention, "updateBest(table);")
        indention -= 1
        write_line(tablefile, indention, "} );")
        indention -= 1
        write_line(tablefile, indention, "")
        indention += 1
        write_line(tablefile, indention, "updateBest(table);")
        indention += 1
        write_line(tablefile, indention, "updateWorst(table);")
        indention -= 1
        write_line(tablefile, indention, "</script>")
        indention -= 1
        write_line(tablefile, indention, "</div>")
        write_line(tablefile, indention, "</body>")
        write_line(tablefile, indention, "</html>")

    path=set_artifact_dir(os.path.join(output_dir, "style.css"))
    with open(path, 'w') as stylefile:
        #        write_line(stylefile, 0, '@import url("{}");'.format(os.path.join(qcomp_root, "fonts/Tajawal/Tajawal.css"))) #TODO
        stylefile.write(r"""

    .best {
        background-color: lightgreen;
    }
    .worst {
        background-color: tomato;
    }
    .error {
    	font-weight: bold;
    	background-color: lightcoral;
    }
    .timeout {
        background-color: lightgray;
    }
    .memout {
        background-color: lightgray;
    }
    .unsupported {
        background-color: yellow;
    }
    .nobaseline {
        background-color: lightblue;
    }
    .notavailable {
        background-color: lightcoral;
    }

    h1 {
    	font-size: 28px; font-weight: bold;
    	color: #000000;
    	padding: 1px; margin-top: 20px; margin-bottom: 1ex;
    }

    tt, .tt {
    	font-family: 'Courier New', monospace; line-height: 1.3;
    }

    .box {
    	margin: 2.5ex 0ex 1ex 0ex; border: 1px solid #D0D0D0; padding: 1.6ex 1.5ex 1ex 1.5ex; position: relative;
    }

    .boxlabelo {
    	position: absolute; pointer-events: none; margin-bottom: 0.5ex;
    }

    .boxlabel {
    	position: relative; top: -3.35ex; left: -0.5ex; padding: 0px 0.5ex; background-color: #FFFFFF; display: inline-block;
    }
    .boxlabelc {
    	position: relative; top: -3.17ex; left: -0.5ex; padding: 0px 0.5ex; background-color: #FFFFFF; display: inline-block;
    }
    """)


def json_results_to_vector(json_path, num_states):
    if not os.path.isfile(set_artifact_dir(json_path)):
        print("Error: File '{}' does not exist.".format(json_path))
        return None

    vector = np.empty(num_states)
    state = 0
    json = open(json_path, 'rb')
    for entry in ijson.items(json, 'item'):
        while state < entry["s"]:
            vector[state] = float(0.0)
            state = state + 1
        if entry["s"] == state:
            if entry["v"] is None: # value is missing
                vector[state] = float(100000000000.0) # hack: this is storm::utility::infinity<RationalNumber>() ...
            else:
                vector[state] = float(entry["v"])
            state = state + 1
        else:
            # something is not right
            print("Error: Missing value for state number'{}' in file '{}'".format(state, json_path))
            return None

    return vector


def generate_comparison_values(exec_data, benchmark_ids, tools_configs_solvers_precisions_baseline,
                               tools_configs_solvers_precisions):
    progressbar = Progressbar(len(benchmark_ids), "Generating comparison values")
    i = 0
    for benchmark_id in benchmark_ids:
        i += 1
        progressbar.print_progress(i)
        # First generate the vector of baseline result:
        # We use the first available value from te baseline benchmarks:
        # benchmark_id -> baseline_result_vector
        baseline_result_vector = None
        for (tool, config, solver, precision) in tools_configs_solvers_precisions_baseline:
            # print("Generate baseline vector via: "+ str((tool, config, solver, precision)))
            if benchmark_id in exec_data[tool][config][solver][precision]:
                res_json = exec_data[tool][config][solver][precision][benchmark_id]
                if "timeout" in res_json and "execution-error" in res_json and "mc-time" in res_json and "export-value-file" in res_json:
                    baseline_result_json_path = res_json["export-value-file"]
                    num_states = int(res_json["states"])
                    if tool.lower() == "storm":
                        baseline_result_vector = json_results_to_vector(baseline_result_json_path, num_states)
                    if baseline_result_vector is not None:
                        # found results, we can stop now
                        break

        if baseline_result_vector is None:
            # print("Baseline for benchmark '{}' does not exist.".format(benchmark_id))
            for (tool, config, solver, precision) in tools_configs_solvers_precisions:
                # No baseline: set norm for each benchmark to NB_VALUE
                if benchmark_id in exec_data[tool][config][solver][precision]:
                    exec_data[tool][config][solver][precision][benchmark_id]["absolute-error-max-norm-value"] = NB_VALUE
                    exec_data[tool][config][solver][precision][benchmark_id]["relative-error-max-norm-value"] = NB_VALUE
                    exec_data[tool][config][solver][precision][benchmark_id]["absolute-error-mean_deviation_value"] = NB_VALUE
                    exec_data[tool][config][solver][precision][benchmark_id]["relative-error-mean_deviation_value"] = NB_VALUE
        else:
            for (tool, config, solver, precision) in tools_configs_solvers_precisions:
                benchmark_result_vector = None
                absolute_error_max_norm_value = NA_VALUE
                relative_error_max_norm_value = NA_VALUE
                absolute_error_mean_deviation_value = NA_VALUE
                relative_error_mean_deviation_value = NA_VALUE

                if benchmark_id in exec_data[tool][config][solver][precision]:
                    res_json = exec_data[tool][config][solver][precision][benchmark_id]
                    if "timeout" in res_json and not res_json["timeout"] and \
                            "execution-error" in res_json and not res_json["execution-error"] and \
                            "export-value-file" in res_json:
                        if not os.path.isfile(set_artifact_dir(res_json["export-value-file"])):
                            print("Error: File '{}' does not exist.".format(set_artifact_dir(res_json["export-value-file"])))
                            print("test")
                            continue
                        # we have a result
                        result_json_path = res_json["export-value-file"]
                        num_states = int(res_json["states"])
                        if tool.lower() == "storm":
                            benchmark_result_vector = json_results_to_vector(result_json_path, num_states)

                        if benchmark_result_vector is not None:
                            ''' max norm '''
                            # get the absolute error
                            # if one of the values is infinity but the other not, the error is set to infinity
                            inf_mask = (benchmark_result_vector != float('inf')) & (baseline_result_vector != float('inf'))
                            absolute_error_diff_vector = np.subtract(benchmark_result_vector, baseline_result_vector,
                                                                     out=np.full(len(benchmark_result_vector),
                                                                                 float('inf')),
                                                                     where=inf_mask)
                            # inf-inf = np.nan, replace this by 0 since the error is 0
                            absolute_error_diff_vector[benchmark_result_vector == baseline_result_vector] = 0
                            absolute_error_max_norm_value = np.linalg.norm(absolute_error_diff_vector, np.inf)

                            # get the relative error, we keep infinity if the absolute error is infinity
                            inf_mask = (baseline_result_vector != float('inf')) & (baseline_result_vector != 0) & (
                                    absolute_error_diff_vector != float('inf'))
                            relative_error_diff_vector = np.divide(absolute_error_diff_vector, baseline_result_vector,
                                                                   out=np.full(len(benchmark_result_vector), float('inf')),
                                                                   where=inf_mask)
                            # set the relative error to 0 if the difference was 0
                            relative_error_diff_vector[absolute_error_diff_vector == 0] = 0
                            relative_error_max_norm_value = np.linalg.norm(relative_error_diff_vector, np.inf)

                            ''' mean deviation '''
                            inf_mask = (absolute_error_diff_vector != float('inf'))
                            absolute_error_mean_deviation_value = np.mean(
                                np.absolute(np.subtract(absolute_error_diff_vector, np.mean(absolute_error_diff_vector),
                                                        out=np.full(len(benchmark_result_vector), float('inf')),
                                                        where=inf_mask)))

                            inf_mask = (relative_error_diff_vector != float('inf'))
                            relative_error_mean_deviation_value = np.mean(
                                np.absolute(np.subtract(relative_error_diff_vector, np.mean(relative_error_diff_vector),
                                                        out=np.full(len(benchmark_result_vector), float('inf')),
                                                        where=inf_mask)))

                    exec_data[tool][config][solver][precision][benchmark_id]["absolute-error-max-norm-value"] = absolute_error_max_norm_value
                    exec_data[tool][config][solver][precision][benchmark_id]["relative-error-max-norm-value"] = relative_error_max_norm_value
                    exec_data[tool][config][solver][precision][benchmark_id]["absolute-error-mean_deviation_value"] = absolute_error_mean_deviation_value
                    exec_data[tool][config][solver][precision][benchmark_id]["relative-error-mean_deviation_value"] = relative_error_mean_deviation_value

    return exec_data


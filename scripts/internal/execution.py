from .utility import *
import subprocess, threading, time

class CommandExecution(object):
    """ Represents the execution of a single command line argument. """

    def __init__(self):
        self.timeout = None
        self.return_code = None
        self.output = None
        self.wall_time = None
        self.proc = None

    def stop(self):
        self.timeout = True
        self.proc.kill()

    def run(self, command_line_str, time_limit):
        command_line_list = command_line_str.split()
        command_line_list[0] = os.path.expanduser(command_line_list[0])
        start_time = time.time()
        self.timeout = False
        self.output = ""
        try:
            self.proc = subprocess.Popen(command_line_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            self.output = "Error when executing the command:\n{}\n".format(e)
            self.wall_time = 0
            self.return_code = -1
            return
        if time_limit is not None and time_limit > 0:
            timer = threading.Timer(time_limit, self.stop)
            timer.start()
        try:
            stdout, stderr = self.proc.communicate()
        except Exception as e:
            self.output = self.output + "Error when executing the command:\n{}\n".format(e)
        finally:
            timer.cancel()
            self.wall_time = time.time() - start_time
            self.return_code = self.proc.returncode
        #  filter for uneccesary warning
        stdout_filtered = ""
        for line in stdout.decode('utf8').splitlines(keepends=True):
            if not "WARN (json.hpp:185): Inaccurate JSON export:" in line:
                stdout_filtered += line

        self.output = self.output + stdout_filtered

        if len(stderr) > 0:
            self.output = self.output + "\n" + "#" * 30 + "Output to stderr" + "#" * 30 + "\n" + stderr.decode('utf8')
        if self.timeout and self.wall_time <= time_limit:
            print(
                "WARN: A timeout was triggered although the measured time is {} seconds which is still below the time limit of {} seconds".format(
                    self.wall_time, time_limit))


def execute_command_line(command_line_str: str, time_limit: int, warm_up_run=False):
    """
    Executes the given command line with the given time limit (in seconds).
    If warm_up_run is true, there will be a warm-up execution with a 5 second time limit (whose results will be discarded) before the actual execution.
    :returns the output of the command (including the output to stderr, if present), the runtime of the command and either the return code or None (in case of a timeout)
    """
    command_line_str = set_artifact_dir(command_line_str)
    if warm_up_run:
        # do a warm-up run first to hopefully decrease file i/o delay
        dryrun = CommandExecution()
        dryrun.run(command_line_str, 5)
    # now start the actual run.
    execution = CommandExecution()
    execution.run(command_line_str, time_limit)
    if execution.timeout:
        return execution.output, execution.wall_time, None
    else:
        return execution.output, execution.wall_time, execution.return_code


class Execution(object):
    def __init__(self, invocation):
        self.invocation = invocation
        self.wall_time = None
        self.logs = None
        self.timeout = None
        self.error = None
        self.return_codes = None

    def run(self, warm_up_run=False):
        self.error = False
        self.timeout = False
        self.wall_time = 0.0
        self.logs = []
        self.return_codes = []

        command = self.invocation.command
        log, wall_time, return_code = execute_command_line(command, self.invocation.time_limit - self.wall_time, warm_up_run)
        self.wall_time = self.wall_time + wall_time
        self.logs.append(
            "Command:\t{}\nWallclock time:\t{}\nReturn code:\t{}\nOutput:\n{}\n".format(command, wall_time,
                                                                                        return_code, log))
        if return_code is None:
            self.timeout = True
            self.error = False
            self.logs[-1] = self.logs[
                                -1] + "\n" + "-" * 10 + "\nComputation aborted after {} seconds since the total time limit of {} seconds was exceeded.\n".format(
                self.wall_time, self.invocation.time_limit)
            self.return_codes.append(-9)  # process got killed due to timeout
        else:
            self.error = self.error or return_code != 0
            self.return_codes.append(return_code)

    def concatenate_logs(self):
        hline = "\n" + "#" * 40 + "\n"
        return hline.join(self.logs)

    def to_json(self):
        res = self.invocation.to_json()
        if self.wall_time is not None:
            res["wallclock-time"] = str(self.wall_time)
        if self.timeout is not None:
            res["timeout"] = self.timeout
        if self.error is not None:
            res["execution-error"] = self.error
        if self.return_codes is not None:
            res["return-codes"] = self.return_codes
        return res

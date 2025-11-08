import os
import sys
import time
import math
import csv
import json
import shutil
from decimal import *
from fractions import *
from collections import OrderedDict


def set_artifact_dir(s : str):
    if os.environ.get('ARTIFACT_DIR') is None:
        artifact_dir = os.path.realpath(os.path.join(sys.path[0], ".."))
    else:
        artifact_dir = os.environ.get('ARTIFACT_DIR')
    return os.path.expandvars(s.replace("$ARTIFACT_DIR", artifact_dir))

def load_json(path: str):
    path = set_artifact_dir(path)
    with open(path, 'r', encoding='utf-8-sig') as json_file:
        return json.load(json_file, object_pairs_hook=OrderedDict)


def save_json(json_data, path: str):
    path = set_artifact_dir(path)
    with open(path, 'w') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent='\t')


def load_csv(path: str, delim='\t'):
    path = set_artifact_dir(path)
    with open(path, 'r') as csv_file:
        return list(csv.reader(csv_file, delimiter=delim))


def save_csv(csv_data, path: str, delim=';'):
    path = set_artifact_dir(path)
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=delim)
        writer.writerows(csv_data)


def ensure_directory(path: str):
    path = set_artifact_dir(path)
    if not os.path.exists(path):
        os.makedirs(path)


def is_valid_filename(name: str, invalid_chars=None):
    name = set_artifact_dir(name)
    if invalid_chars is not None:
        for c in invalid_chars:
            if c in name:
                return False
    try:
        if os.path.isfile(name):
            return True
        open(name, 'a').close()
        os.remove(name)
    except IOError:
        return False
    return True


def remove_directory_contents(directory, exluded=[]):
    directory = set_artifact_dir(directory)
    for name in os.listdir(directory):
        if name not in exluded:
            try:
                path = os.path.join(directory, name)
                remove_file_or_dir(path)
            except Exception:
                print("Unable to remove '{}'".format(path))


def remove_file_or_dir(name):
    name = set_artifact_dir(name)
    if os.path.isdir(name):
        shutil.rmtree(name)
    else:
        os.remove(name)


def is_bool(expr):
    if isinstance(expr, bool):
        return True
    try:
        return expr.lower() in ["true", "false"]
    except:
        return False


def is_inf(expr):
    try:
        return math.isinf(Decimal(expr))
    except Exception:
        return False


def is_number(expr):
    if is_bool(expr):
        return False
    if is_inf(expr):
        return True
    try:
        Fraction(expr)
    except Exception:
        return False
    return True


def is_interval(expr):
    try:
        if is_number(expr["lower"]) and is_number(expr["upper"]):
            return True
    except (InvalidOperation, KeyError, TypeError):
        pass
    return False


def is_number_or_interval(expr):
    return is_number(expr) or is_interval(expr)


def try_to_number(expr):
    if is_number(expr):
        if is_inf(expr):
            return Decimal(expr)
        else:
            return Fraction(expr)
    try:
        return try_to_number(expr["num"]) / try_to_number(expr["den"])
    except Exception:
        return expr


def try_to_bool_or_number(expr):
    if is_bool(expr):
        if (isinstance(expr, str)):
            if expr.lower() == "true":
                return True
            elif expr.lower() == "false":
                return False
        return bool(expr)
    return try_to_number(expr)


def get_decimal_representation(number):
    if is_number(number):
        return Decimal(number)
    else:
        return Decimal(number["num"]) / Decimal(number["den"])


def try_to_float(expr):
    # expr might be too large for float
    try:
        return float(expr)
    except Exception:
        return expr


class Progressbar(object):
    def __init__(self, max_value, label="Progress", width=50, delay=0.5):
        self.progress = 0
        self.max_value = max_value
        self.label = label
        self.width = width
        self.delay = delay
        self.last_time_printed = time.time()
        sys.stdout.write("\n")
        self.print_progress(0)

    def print_progress(self, value):
        now = time.time()
        if now - self.last_time_printed >= self.delay or value == self.max_value or value == 0:
            if (self.max_value == 0):
                progress = self.width
            else:
                progress = (value * self.width) // self.max_value
            sys.stdout.write(
                "\r{}: [{}{}] {}/{} ".format(self.label, '#' * progress, ' ' * (self.width - progress), value,
                                             self.max_value))
            sys.stdout.flush()
            self.last_time_printed = now
            return True
        return False


def command_line_input(item: str, options: OrderedDict, single_choice=False):
    if not single_choice:
        if "a" in options: raise AssertionError("options should not include key 'a'")
        if "d" in options: raise AssertionError("options should not include key 'd'")
        if "c" in options: raise AssertionError("options should not include key 'c'")
    if len(options) == 0: raise AssertionError("options should not be empty.")
    longest_option_descriptions = []
    longest_option_descriptions.append(max([len(key) for key in options] + [4]) + 4)
    i = 0
    while True:
        longest = -1
        for key in options:
            if i < len(options[key]):
                longest = max(longest, len(options[key][i]))
        if longest >= 0:
            longest_option_descriptions.append(longest + 4)
        else:
            break
        i += 1

    selected_keys = []
    while True:
        keys = []
        print("Select {}.".format(item))
        print("    Option" + " " * (longest_option_descriptions[0] - len("Option")) + "Description")
        print("----" + "-" * sum(longest_option_descriptions))
        for key in options:
            keys.append(key)
            description = ""
            for i in range(len(options[key])):
                description += "{}{}".format(options[key][i],
                                             " " * (longest_option_descriptions[i + 1] - len(options[key][i])))
            print("{}{}{}".format("[X] " if key in selected_keys else "[ ] ",
                                  key + " " * (longest_option_descriptions[0] - len(key)), description))
        if not single_choice:
            keys.append("a")
            print("    {}Select all".format("a" + " " * (longest_option_descriptions[0] - 1)))
        if not single_choice and len(selected_keys) > 0:
            keys.append("c")
            print("    {}Clear selection".format("c" + " " * (longest_option_descriptions[0] - 1)))
            keys.append("d")
            print("    {}done".format("d" + " " * (longest_option_descriptions[0] - 1)))
        selection = input("Enter option: ")
        if selection in keys:
            if selection in options:
                selected_keys.append(selection)
                if single_choice:
                    break
            elif selection == "a":
                selected_keys = keys[:len(options)]
                break
            elif selection == "d":
                break
            elif selection == "c":
                selected_keys = []
        else:
            print("Invalid selection. Enter any of {} or press Ctrl+C to abort.".format(keys))
    print("Selected {}: {}".format(item, selected_keys))
    return selected_keys


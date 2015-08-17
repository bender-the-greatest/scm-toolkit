#!/usr/bin/env python3 -tt
__author__ = 'alexa'

import sys
import os
from subprocess import Popen, PIPE
from time import sleep
import argparse

# Bin paths
svnadmin_bin = '/usr/bin/svnadmin'

# Global vars
__verbose = False
__repo_dir = '/var/lib/scm/repositories/svn'


# Functions
def verify_repository(repo_path):
    p = Popen([svnadmin_bin,
               'verify',
               repo_path], stdout=PIPE, stderr=PIPE)
    output = []
    error = []
    while p.poll() is None:
        sleep(1)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Svnadmin verify failed with return code {}".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return False
    elif __verbose:
        print(' '.join(output))
    return True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                        help='Display more verbose output.')
    parser.add_argument('-d', '--directory', dest='directory', type=str, default=__repo_dir,
                        help='Path to the repositories directory.')
    parser.add_argument('-b', '--svnadmin', dest='svnadmin_bin', type=str, default=svnadmin_bin)
    args = parser.parse_args()
    # Set verbose flag
    global __verbose
    __verbose = args.verbose
    # Set repo dir
    global __repo_dir
    __repo_dir = args.directory
    # Set svnadmin bin
    global svnadmin_bin
    svnadmin_bin = args.svnadmin_bin


def process_output(file):
    output = file.read().split()
    for x in range(0, len(output)):
        output[x] = output[x].decode()
    return output


def append_to_list(original_list, list_to_append):
    for i in list_to_append:
        original_list.append(i)


def get_repository_list(dir_path):
    return os.listdir(dir_path)


def check_paths():
    if not os.path.exists(svnadmin_bin):
        return "Can't find svnadmin binary at {}.".format(svnadmin_bin)
    if not os.path.exists(__repo_dir):
        return "Repository directory path does not exist at {}".format(__repo_dir)
    return None


# Main function
def __main():
    print("Getting list of repositories at {}...".format(__repo_dir))
    try:
        repo_list = get_repository_list(__repo_dir)
    except FileNotFoundError as err:
        print(("Repository directory not found at '{}'. Please verify that the directory exists and that you have "
               "permission to access it.".format(__repo_dir)), file=sys.stderr)
        return -2
    except NotADirectoryError as err2:
        print(
            "The specified repository directory '{}' is not a directory. Please check your path and try again.".format(
                __repo_dir), file=sys.stderr)
        return -3
    print("Beginning repository verification process...")
    for repo_name in repo_list:
        print()
        print("Verifying {}".format(repo_name))
        full_path = os.path.join(__repo_dir, repo_name)
        if verify_repository(full_path):
            print("{} verified successfully!".format(repo_name))
        else:
            print("{} failed to verify.".format(repo_name), file=sys.stderr)
    return 0


# Entry point
if __name__ == '__main__':
    parse_args()
    check = check_paths()
    if check is None:
        sys.exit(__main())
    else:
        print(check)
        sys.exit(-1)

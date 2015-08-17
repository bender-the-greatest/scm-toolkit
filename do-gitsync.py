#!/usr/bin/env python3 -tt
import sys
import os
from subprocess import Popen, PIPE
from time import sleep
from collections import Iterable
import argparse

# Bin Paths
ssh_bin = "/usr/bin/ssh"
git_bin = "/usr/bin/git"

# Global Vars
server_name = "server.domain.tld"
user_name = "username"
pass_word = r"password"
ssh_user_name = "ssh_username"
local_repo_directory = "/repositories/git/"
sleep_time_seconds = 0.1
__verbose = False


# Functions
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Display more verbose output')
    parser.set_defaults(verbose=False)
    args = parser.parse_args()
    # Set verbose flag
    global __verbose
    __verbose = args.verbose


def check_paths():
    if not os.path.exists(ssh_bin):
        return "Can't find SSH client at {}".format(ssh_bin)
    if not os.path.exists(git_bin):
        return "Can't find git binary at {}".format(git_bin)
    if not os.path.isdir(local_repo_directory):
        return "Can't find local repository directory at {}".format(local_repo_directory)
    return None


def process_output(file):
    output = file.read().split()
    for x in range(0, len(output)):
        output[x] = output[x].decode()
    return output


def append_to_list(original_list, list_to_append):
    for i in list_to_append:
        original_list.append(i)


def get_remote_dir_names():
    p = Popen([ssh_bin,
               '{}@{}'.format(
                   ssh_user_name,
                   server_name
               ),
               'find',
               '/var/lib/scm/repositories/git/',
               '-maxdepth', '1',
               '-type', 'd',
               '-exec', 'basename {} \;'], stdout=PIPE, stderr=PIPE)
    # Safely process the output
    output = []
    error = []
    while p.poll() is None:
        sleep(sleep_time_seconds)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Failed to list remote directories with return code {}".format(p.returncode), sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return None
    elif __verbose:
        print(' '.join(output))
    return output


def do_git_fetch(path):
    p = Popen([git_bin,
               '-C',
               '%s' % path,
               'fetch',
               '-v'], stdout=PIPE, stderr=PIPE)
    # Safely process the output
    output = []
    error = []
    while p.poll() is None:
        sleep(sleep_time_seconds)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Git fetch failed with return code {}.".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return False
    elif __verbose:
        print(' '.join(output))
    return True


def do_git_clone(url, path):
    p = Popen([git_bin,
               'clone',
               '--mirror',
               url,
               '%s' % path], stdout=PIPE, stderr=PIPE)
    # Safely process the output
    output = []
    error = []
    while p.poll() is None:
        sleep(sleep_time_seconds)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Git clone failed with return code {}.".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return False
    elif __verbose:
        print(' '.join(output))
    return True


# Main Function
def main():
    print("Enumerating directories from {}".format(server_name))
    names = get_remote_dir_names()
    if names is None:
        sys.exit(-2)
    names = [n for n in names if not n.startswith('git')]
    print("Directory listing from {} succeeded!".format(server_name))

    for n in names:
        print()
        n_path = local_repo_directory + n + '/'
        url = "https://{}/scm/git/{}".format(
            server_name,
            n
        )
        url_with_creds = "https://{}:{}@{}/scm/git/{}".format(
            user_name,
            pass_word,
            server_name,
            n
        )
        if os.path.isdir(n_path):
            print("Synchronizing {}...".format(n))
            print("Remote URL is {}. Starting fetch...".format(url))
            ret = do_git_fetch(n_path)
            if not ret:
                print("Project {} failed to sync.".format(n), file=sys.stderr)
            else:
                print("Project {} synchronized successfully!".format(n))
        else:
            print("First time synchronization on new project {}".format(n), file=sys.stderr)
            print("Remote URL is {}. Cloning as git mirror...".format(url), file=sys.stderr)
            ret = do_git_clone(url_with_creds, n_path)
            if not ret:
                print("Project {} failed to sync.".format(n), file=sys.stderr)
            else:
                print("Project {} synchronized successfully!".format(n))


if __name__ == '__main__':
    check = check_paths()
    parse_args()
    if check is None:
        main()
    else:
        print(check, file=sys.stderr)
        sys.exit(-1)

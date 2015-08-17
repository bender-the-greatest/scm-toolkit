#!/usr/bin/env python3 -tt
import sys
import os
from subprocess import Popen, PIPE
from time import sleep
import argparse

# Bin Paths
ssh_bin = "/usr/bin/ssh"
svnsync_bin = "/usr/local/bin/svnsync"
svnadmin_bin = "/usr/local/bin/svnadmin"
svnlook_bin = "/usr/local/bin/svnlook"

# SVN HTTP client (this MUST be set to 'serf' if using svn 1.8 or later)
# However, the 'svnsync sync' command seems to have issues communicating with SCM Manager
# using the 'serf' client.
svn_http_client = 'neon'

# Global Vars
server_name = "server.domain.tld"
user_name = "username"
pass_word = r"password"
ssh_user_name = "ssh_username"
local_repo_directory = "/repositories/svn/"
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
    if not os.path.exists(svnsync_bin):
        return "Can't find svnsync binary at {}".format(svnsync_bin)
    if not os.path.exists(svnadmin_bin):
        return "Can't find svnadmin binary at {}".format(svnadmin_bin)
    if not os.path.exists(svnlook_bin):
        return "Can't find svnlook binary at {}".format(svnlook_bin)
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
               '/var/lib/scm/repositories/svn/',
               '-maxdepth', '1',
               '-type', 'd',
               '-exec', 'basename {} \;'], stdout=PIPE, stderr=PIPE)
    output = []
    error = []
    while p.poll() is None:
        sleep(1)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Failed to list remote directories with return code {}".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return None
    elif __verbose:
        print(' '.join(output))
    return output


def sync_repo(path):
    # Sync existing mirror with new changes
    p = Popen([svnsync_bin,
               'sync',
               '--username',
               user_name,
               '--password',
               pass_word,
               '--config-option=servers:global:http-library={}'.format(svn_http_client),
               'file://{}'.format(path)], stdout=PIPE, stderr=PIPE)
    output = []
    error = []
    while p.poll() is None:
        sleep(1)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Svnsync sync failed with return code {}".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return False
    elif __verbose:
        print(' '.join(output))
    return True


def create_sync_repo(path, url):
    # Create new repository
    p = Popen([svnadmin_bin,
               'create',
               path], stdout=PIPE, stderr=PIPE)
    output = []
    error = []
    while p.poll() is None:
        sleep(1)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Svnadmin create failed with return code {}".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return False
    if __verbose:
        print(' '.join(output))
    revprop_path = None
    # Prep for svnsync
    try:
        # Make sure pre-revprop-change has content
        revprop_path = "{}/hooks/pre-revprop-change".format(path)
        with open(revprop_path, 'w') as out:
            out.write("#!/bin/sh")
        p = Popen(['chmod',
                   '755',
                   revprop_path], stdout=PIPE, stderr=PIPE)
        # Safely process the output
        output = []
        error = []
        while p.poll() is None:
            sleep(1)
            append_to_list(output, process_output(p.stdout))
            append_to_list(error, process_output(p.stderr))
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
        if not p.returncode == 0:
            print("chmod 755 failed with return code {}".format(p.returncode), file=sys.stderr)
            print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
            print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
            return False
        elif __verbose:
            print(' '.join(output))
    except IOError as err:
        print("An error occurred while writing to {} with error code {}: {}".format(
            revprop_path, err.errno, err.output), file=sys.stderr)
        return False
    # Now we're ready for svnsync init
    p = Popen([svnsync_bin,
               'init',
               '--username',
               user_name,
               '--password',
               pass_word,
               'file://{}'.format(path),
               url], stdout=PIPE, stderr=PIPE)
    # Safely process the output
    output = []
    error = []
    while p.poll() is None:
        sleep(1)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not (p.returncode == 0 or p.returncode == 1):
        print("Svnsync init failed with return code {}".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return False
    elif __verbose:
        print(p.stdout.readlines())
    p = Popen([svnlook_bin,
               'pg',
               '--revprop',
               '-r0',
               path,
               r'svn:sync-from-uuid'], stdout=PIPE, stderr=PIPE)
    # Safely process the output
    output = []
    error = []
    while p.poll() is None:
        sleep(1)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Svnlook pg failed with return code {}".format(p.returncode), file=sys.stderr)
        print("Process Output: {}".format(' '.join(output)), file=sys.stderr)
        print("Error Output: {}".format(' '.join(error)), file=sys.stderr)
        return False
    # Don't worry about displaying the output of svnlook pg, only contains a uuid if it succeeds
    # Speaking of which, set uuid to the output
    uuid = ''.join(output)
    p = Popen([svnadmin_bin,
               'setuuid',
               path,
               uuid], stdout=PIPE, stderr=PIPE)
    # Safely process the output
    output = []
    error = []
    while p.poll() is None:
        sleep(1)
        append_to_list(output, process_output(p.stdout))
        append_to_list(error, process_output(p.stderr))
    append_to_list(output, process_output(p.stdout))
    append_to_list(error, process_output(p.stderr))
    if not p.returncode == 0:
        print("Svnadmin setuuid failed with return code {}".format(p.returncode), file=sys.stderr)
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
    names = [n for n in names if not n.startswith('svn')]
    print("Directory listing from {} succeeded!".format(server_name))
    for n in names:
        print()
        n_path = local_repo_directory + n + '/'
        url = "https://{}/scm/svn/{}".format(
            server_name,
            n
        )
        if os.path.isdir(n_path):
            print("Synchronizing {}...".format(n))
            print("Remote URL is {}. Starting svnsync sync...".format(url))
            ret = sync_repo(n_path)
            if not ret:
                print("Project {} failed to sync.".format(n))
                continue
        else:
            print("First time synchronization on new project {}".format(n))
            print(("Remote URL is {}. Initializing mirror repository if necessary"
                   " and performing initial sync...".format(url)))
            ret = create_sync_repo(n_path, url)
            if not ret:
                print("Project {} failed to sync.".format(n), file=sys.stderr)
                continue
            ret = sync_repo(n_path)
            if not ret:
                print("Project {} failed to sync.".format(n), file=sys.stderr)
                continue


# Entry Point
if __name__ == '__main__':
    check = check_paths()
    parse_args()
    if check is None:
        main()
    else:
        print(check)
        sys.exit(-1)

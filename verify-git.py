import sys
import os
from subprocess import Popen, PIPE
from time import sleep
import argparse

# Bin paths
git_bin = '/usr/bin/git'

# Global vars
__verbose = False
__repo_dir = '/repositories/git'
__should_gc = False


# Functions
def verify_repository(repo_path, should_gc=__should_gc):
    # Set vars
    global __verbose
    old_dir = os.getcwd()
    nullpipe = open(os.devnull, "w")

    # Change to the repository path
    try:
        os.chdir(repo_path)
    except FileNotFoundError as err:
        print("Error: The repository path {} does not exist!".format(repo_path), file=sys.stderr)
        os.chdir(old_dir)
        return False
    except NotADirectoryError as err2:
        print("Error: The repository path {} is not a directory".format(repo_path), file=sys.stderr)
        os.chdir(old_dir)
        return False

    # Run git gc (don't stop if it fails, because 'git gc' may return a non-zero on a warning
    # and is rather undocumented)
    if should_gc:
        print("Running 'git gc'. Even if this fails, the integrity check will still continue.", file=sys.stdout)
        p = Popen([git_bin,
                   'gc'], stdout=nullpipe, stderr=nullpipe)
        p.wait()
        if not p.returncode == 0:
            print(
                "Git gc failed with return code {}. It is recommended to run 'git gc' manually"
                " to check the output.".format(p.returncode), file=sys.stderr)
        else:
            print("Git gc completed successfully!", file=sys.stdout)
        print("Continuing with integrity check of repository.", file=sys.stdout)
    # Run git fsck
    p = Popen([git_bin,
               'fsck'], stdout=nullpipe, stderr=nullpipe)
    p.wait()
    if not p.returncode == 0:
        print("Git fsck failed with return code {}.".format(p.returncode), file=sys.stderr)
        os.chdir(old_dir)
        return False
    print("Git fsck completed successfully!", file=sys.stdout)
    os.chdir(old_dir)
    return True


def parse_args():
    global __verbose
    global __repo_dir
    global git_bin
    global __should_gc

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                        help='Display more verbose output.')
    parser.add_argument('-d', '--directory', dest='directory', type=str, default=__repo_dir,
                        help='Path to the repositories directory.')
    parser.add_argument('-b', '--git', dest='git_bin', type=str, default=git_bin,
                        help='Path to the git binary.')
    parser.add_argument('-gc', '--garbage-collect', dest='gc', action='store_true', default=False,
                        help='If set, "git gc" will be run prior to any integrity checks.')
    args = parser.parse_args()
    # Set verbose flag
    __verbose = args.verbose
    # Set repo dir
    __repo_dir = args.directory
    # Set git bin
    git_bin = args.git_bin
    # Set GC flag
    __should_gc = args.gc


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
    global __repo_dir
    if not os.path.exists(git_bin):
        return "Can't find git binary at {}.".format(git_bin)
    if not os.path.exists(__repo_dir):
        return "Repository directory path does not exist at {}".format(__repo_dir)
    return None


# Main function
def __main():
    global __repo_dir
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
        print("Verifying {}...".format(repo_name))
        full_path = os.path.join(__repo_dir, repo_name)
        if verify_repository(full_path):
            print("{} verified successfully!".format(repo_name), file=sys.stdout)
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

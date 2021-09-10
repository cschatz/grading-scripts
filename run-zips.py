#!/usr/local/bin/python

import sys, glob, os, re
from utils import *

skip_commented = False

GRADING_DIR = "/Users/cschatz/thumper/grading"

build_dir = ""

def run_one(filename):
    global skip_commented
    dir = os.path.dirname(filename)
    pat = re.compile('(((\w|-)+)_(\d+)_(\d+)_(.+)).zip')
    m = pat.match(os.path.basename(filename))
    if m:
        stem = m.group(1)
        print "--- {} ---".format(stem)
        executable = dir + "/" + stem + ".prog"
        comments = dir + "/" + stem + ".comments"
        src_dir = dir + "/" + stem + ".dir"
        if skip_commented and os.path.isfile(comments):
            print "[Skipping!]\n".format(stem)
            return
        default = "r"
        while True:
            choice = get_choice(["run", "rebuild", "edit", "comment", "good", "done"], ["r", "rr", "e", "c", "g", "d"], default)
            if choice == "e":
                os.system("emacs '{}/main.cpp'".format(build_dir))
                default = "c"
            elif choice == "r" or choice == "rr":
                exec_exists = False
                if choice == "r":
                    print "Checking for", executable
                    if os.path.isfile(executable):
                        print "Executable exists already."
                        exec_exists = True
                    else:
                        print "No executable - need to build."
                if not exec_exists:
                    print "Unzipping..."
                    os.system("unzip -jo -d '{}' '{}'".format(src_dir, filename))
                    print "Prepping build dir..."
                    os.system("find {} -mindepth 1 -not -type l | xargs rm".format(build_dir))
                    os.system("cp '{}'/* {}".format(src_dir, build_dir))
                    os.system("cd '{}' && make".format(build_dir))
                    os.system("cp '{}'/prog '{}'".format(build_dir, executable))
                os.system("clear && '{}'".format(executable))
                default = "c"
            elif choice == "c":
                os.system("emacs '" + comments + "'")
                default = "d"
            elif choice == "g":
                os.system("echo 'Good.' > '" + comments + "'")
                print "** Ok, comments now say 'Good.'"
                default = "d"
            elif choice == "d":
                return
    else:
        print "*** Doesn't seem to be a submission, skipping. ***"


if (len(sys.argv) < 3):
    print "Args: course assignment [-s]"
    sys.exit()

if len(sys.argv) > 3 and sys.argv[3] == "-s":
    print "Skipping submissions with comments"
    skip_commented = True

subs_dir = "{}/{}/{}".format(GRADING_DIR, sys.argv[1], sys.argv[2])
build_dir = subs_dir + "/_BUILD"
files = glob.glob(subs_dir + "/*.zip")
for file in files:
    # print file
    count = len(glob.glob(subs_dir + "/*.comments"))
    print "{} / {} ({:.1f}% left)".format(count, len(files), 100*(1-1.0*count/len(files)))
    run_one(file)


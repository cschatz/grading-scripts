#!/usr/local/bin/python

import sys, glob, os, re
from utils import *

skip_commented = False

GRADING_DIR = "/Users/cschatz//thumper/grading"

def run_one(filename):
    global skip_commented
    print "File '{}'".format(os.path.basename(filename))
    dir = os.path.dirname(filename)
    pat = re.compile('(((\w|-)+)_(\d+)_(\d+)_(.+)).py')
    m = pat.match(os.path.basename(filename))
    if m:
        stem = m.group(1)
        print "--- {} ---".format(stem)
        executable = dir + "/" + stem + ".prog"
        comments = dir + "/" + stem + ".comments"
        if skip_commented and os.path.isfile(comments):
            print "[Skipping!]\n".format(stem)
            return      
        default = "r"
        while True:
            choice = get_choice(["run", "edit", "comment", "good", "done"], ["r", "e", "c", "g", "d"], default)
            if choice == "e":
                os.system("emacs '" + filename + "'")
                default = "d"
            elif choice == "r":
                os.system("clear")
                os.system("python '" + filename + "'")
                default = "d"
            elif choice == "c":
                os.system("emacs '" + comments + "'")
                default = "d"
            elif choice == "g":
                os.system("echo 'Good.' > '" + comments + "'")
                print "** Ok, comments now say 'Good.'"
                default = "d"
            elif choice == "d":
                return

if (len(sys.argv) < 3):
    print "Args: course assignment [-s]"
    sys.exit()

if len(sys.argv) > 3 and sys.argv[3] == "-s":
    print "Skipping submissions with comments"
    skip_commented = True

subs_dir = "{}/{}/{}".format(GRADING_DIR, sys.argv[1], sys.argv[2])
files = glob.glob(subs_dir + "/*.py")
for file in files:
    print file
    run_one(file)


#!/usr/bin/env python
import sys, glob, os, re, subprocess
from utils import *

GRADING_DIR = "/Users/cschatz/Google Drive/grading"

num_submissions = 0
current = 0
logging = False

def between_submissions():
    for i in range(3):
        print

if len(sys.argv) < 3:
    print "Args: course assignment [-l]"
    sys.exit()

if len(sys.argv) == 4 and sys.argv[3] == "-l":
    logging = True
    print("LOGGING ON")


course, assignment = sys.argv[1:3]
root = GRADING_DIR + "/" + course + "/" + assignment

if not os.path.isdir(root):
    print "*** No submissions directory found."
    sys.exit()

root = GRADING_DIR + "/" + course + "/" + assignment
os.chdir(root)

files = sorted(glob.glob('*.java'))

num_submissions = len(files)

has_footer = os.path.isfile("_footer")

while True:
    file = files[current]
    name = file.split("_")[0]
    print "=========="
    print " Submission {}/{}   {}".format(current+1, num_submissions, name)
    print " (,)back (.)forward (#)jump"
    print " (Q)quit    (enter)run   (e)edit"
    action = raw_input("====> ").lower()
    if action == 'q':
        break
    elif action.isdigit():
        current = int(action)-1
        if current < 0:
            current = 0
        if current >= num_submissions:
            current = num_submissions-1
    elif action == ",":
        current = (current + num_submissions - 1) % num_submissions
    elif action == ".":
        current = (current + 1) % num_submissions
    elif action == "e":
        os.system ("emacs '{}'".format(file))
    elif action == "":
        if has_footer:
            os.system("cat '{}' _footer > _testing/this.java".format(file))
        print
        if logging:
            if has_footer:
                os.system ("java _testing/this.java > '{}'".format(name + ".comments"))
            else:
                os.system ("java '{}' > '{}'".format(file, name + ".comments"))
            os.system ("emacs '{}'".format(name + ".comments"))
        else:
            if has_footer: 
                os.system ("java _testing/this.java")
            else:
                os.system ("java '{}'".format(file))
        print

print
print "===== Program end ====="
print 

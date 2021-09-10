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

if len(sys.argv) < 4:
    print "Args: course assignment filename [-l]"
    sys.exit()

if len(sys.argv) == 5 and sys.argv[4] == "-l":
    logging = True
    print("LOGGING ON")


course, assignment, classfile = sys.argv[1:4]
root = GRADING_DIR + "/" + course + "/" + assignment

if not os.path.isdir(root):
    print "*** No submissions directory found."
    sys.exit()

root = GRADING_DIR + "/" + course + "/" + assignment
os.chdir(root)

files = sorted(glob.glob('*.java'))

num_submissions = len(files)

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
        print
        os.system("cp '{}' '_testing/{}'".format(file, classfile))
        x = os.system("javac _testing/*.java");
        if (x != 0):
            continue
        if logging:
            os.system ("cd _testing; java SchatzMain > '{}'".format(name + ".comments"))
            os.system ("emacs '{}'".format(name + ".comments"))
        else:
            os.system ("cd _testing; java SchatzMain")
        print

print
print "===== Program end ====="
print 

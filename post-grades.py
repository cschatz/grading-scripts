#!/usr/bin/env python

from canvas import *
import sys, json, glob, re, os

GRADING_DIR = "/Users/cschatz/scinet/grading"
TERM = "Fall 2019"


def parse_deductions(filename):
    total = 0
    f = open(filename, "r")
    pat = re.compile('^-(\d+(.\d+)?)$')
    pat2 = re.compile('^\+(\d+(.\d+)?)$')
    for line in f:
        line = line.strip()
        if line == "=====":
            break
        m = pat.match(line)
        m2 = pat2.match(line)
        if m:
            total += float(m.group(1))
        if m2:
            total -= float(m2.group(1))
    return total


if (len(sys.argv) != 3):
    print "Args: course assignment"
    sys.exit()

which_course = sys.argv[1]
which_assignment = sys.argv[2]


print "Determining course ID..."
course_id = find_course_id(which_course)
print "   Found:", course_id

print

print "Determining assignment ID..."
(assignment_id, max_score) = find_assignment_id(course_id, which_assignment)
print "   Found:", assignment_id
print "   Max points:", max_score

print 

all_scores = {}
all_comments = {}

print "Processing comments..."
subs_dir = "{}/{}/{}/_submissions".format(GRADING_DIR, sys.argv[1], sys.argv[2])
os.chdir(subs_dir)
files = glob.glob("*.comments")
pat = re.compile('(\d+)-(\w+)\.comments')
for filename in files:
    m = pat.match(filename)
    if m:
        submission_id = int(m.group(1))
        name = m.group(2)
        fp = open(filename, "r")
        contents = fp.read()
        points = float(max_score) - parse_deductions(filename)
        if points < 0:
            points = 0
        print points, "->", name
        all_scores[submission_id] = points
        all_comments[submission_id] = contents
        # print points
             
print "Done processing comments."

print 

print "Pushing grades and comments..."

"""
OLD WAY!
For some reason on Mills' Canvas server this accepts the scores
but not the comments
for k in all_scores:
    print k
    payload["grade_data[{}][posted_grade]".format(k + COLLEGE_CONSTANT)] = str(all_scores[k])
    payload["grade_data[{}][text_comment]".format(k + COLLEGE_CONSTANT)] = all_comments[k]
result = do_request("post", "courses/{}/assignments/{}/submissions/update_grades".format(course_id, assignment_id), payload)
print "Done pushing to server."
print
print "API returned workflow state:", result['workflow_state']
"""

for k in all_scores:
    print k
    payload = {}
    payload["comment[text_comment]"] = all_comments[k]
    payload["submission[posted_grade]"] = all_scores[k]
    result = do_request("put", "courses/{}/assignments/{}/submissions/{}".format(course_id, assignment_id, k + COLLEGE_CONSTANT), payload)
    print "  ->", result['workflow_state']

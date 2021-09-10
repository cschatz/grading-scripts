#!/usr/bin/env python

from canvas import *
import sys, json, glob, re, os

if len(sys.argv) < 2:
    print "*** Need to give course code"
    exit(-1)

course_code = sys.argv[1]
assignment_name = None


if len(sys.argv) == 3:
    assignment_name = sys.argv[2]

print "Determining course ID..."
course_id = find_course_id(course_code)
print "  done:", course_id

print

if not assignment_name:
    print "ASSIGNMENTS (published)"
    assignments = get_response("courses/{}/assignments".format(course_id))
    for item in assignments:
        if item['published']:
            print "{}: {}".format(item['id'],item['name'])
else:
    print "Determining assignment ID..."
    a_id, max_points = find_assignment_id(course_id, assignment_name)
    print "  done."
    print "ID {}, max points {}".format(a_id, max_points)
    print
    print "Finding submissions..."
    subs = get_response("courses/{}/assignments/{}/submissions".format(course_id, a_id))
    for item in subs:
#        print item
        if item['submitted_at']:
#            print item['user_id']
#            for k in item:
#                print "  {}:{}".format( k, item[k] )
            #print item['user_id']-COLLEGE_CONSTANT, item['attempt'], item['submitted_at']
            
            print item['user_id'], item['submitted_at'].replace("Z", " ").replace("T", " "), item['seconds_late'], item['late_policy_status']
#    print "   ", (item['user_id'] - COLLEGE_CONSTANT)

"""
print "Determining assignment ID...",
(assignment_id, max_score) = find_assignment_id(course_id, which_assignment)
print assignment_id, "Max:", max_score

all_scores = {}
all_comments = {}

subs_dir = "{}/{}/{}".format(GRADING_DIR, sys.argv[1], sys.argv[2])
files = glob.glob(subs_dir + "/*.comments")
pat = re.compile('.+_(\d+)_(\d+)')
for filename in files:
    m = pat.match(os.path.basename(filename))
    if m:
        submission_id = int(m.group(1))
        fp = open(filename, "r")
        contents = fp.read()
        points = float(max_score) - parse_deductions(filename)
        if points < 0:
            points = 0
        print submission_id, "->", points
        all_scores[submission_id] = points
        all_comments[submission_id] = contents
     
print

print "Pushing grades and comments..."
payload = {}
for k in all_scores:
    print k
    payload["grade_data[{}][posted_grade]".format(k)] = str(all_scores[k])
    payload["grade_data[{}][text_comment]".format(k)] = all_comments[k]
result = do_request("post", "courses/{}/assignments/{}/submissions/update_grades".format(course_id, assignment_id), payload)
print "API returned this result:"    
print json.dumps(result)
"""

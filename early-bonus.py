#!/usr/bin/env python3

from canvas import *
import sys, json, glob, re, os
import datetime as dt
import arrow

GRADING_DIR = "/Users/cschatz/thumper/grading"
TERM = "Spring 2019"

if len(sys.argv) not in (3, 4):
    print ("Args: course assignment [days-old]")
    sys.exit()

# Objects for deadline info
section_list = []
deadlines = {}  # section IDs are the keys

# Settings from arguments
which_course = sys.argv[1]
which_assignment = sys.argv[2]
day_limit = None
ago = None
if len(sys.argv) == 4:
    day_limit = sys.argv[3]
    print ("Got day limit: {}".format(day_limit))
    now = dt.datetime.now()
    ago = now-dt.timedelta(days=int(day_limit))

print ("Finding course...")
course_id = find_course_id("Computer Science " + which_course[2:], TERM)
print(course_id)

section_data = get_response("courses/{}/sections".format(course_id))
for s in section_data:
    section_list.append(s['id'])

print ("Finding assignment...")
(assignment_id, max_score) = find_assignment_id(course_id, which_assignment)
bonus_amount = max_score * 0.05

print()
print("Max:", max_score, "Early bonus:", bonus_amount)
print()

assignment = get_response("courses/{}/assignments/{}".format(course_id, assignment_id))
if (assignment['has_overrides']):
	overrides = get_response("courses/{}/assignments/{}/overrides".format(course_id, assignment_id))
	for o in overrides:
		deadlines[o['course_section_id']] = o['due_at']
else:
	for s in section_list:
            deadlines[s] = assignment['due_at']


payload = {}  # data payload for score / comment updates

for section_id in deadlines:
    print ("Section ID {} - deadline: {}".format(section_id, deadlines[section_id]))    
    submissions = get_response("sections/{}/assignments/{}/submissions".format(section_id, assignment_id))
    for s in submissions:
        if s['submitted_at'] != None:
            diff = arrow.get(s['submitted_at'])-arrow.get(deadlines[section_id])
            hrs = (diff.days*3600*24 + diff.seconds) / 3600.0
            if hrs <= -24:
                print ("    {} EARLY ({:.0f} hrs, current score {})".format(s['user_id'], -hrs, s['score']))
                payload["grade_data[{}][posted_grade]".format(s['user_id'])] = str(s['score'] + bonus_amount)
                payload["grade_data[{}][text_comment]".format(s['user_id'])] = "Bonus for early submission"

print("Pushing grades and comments...")

result = do_request("post", "courses/{}/assignments/{}/submissions/update_grades".format(course_id, assignment_id), payload)
print ("API returned this result:") 
print (json.dumps(result))


#!/usr/bin/env python3

from canvas import *
from collections import defaultdict
import sys, os, arrow, math, re

TERM = "Fall 2019"
GRACE_PERIOD = 15 # minutes
PASSES_ALLOWED = 5

if len(sys.argv) < 2:
    print ("Args: course assignment-prefixes")
    sys.exit()

assignment_prefixes = sys.argv[2:]

print (assignment_prefixes)

def short_name(full_name):
    colon = full_name.find(':')
    if colon == -1:
        return full_name
    else:
        return full_name[0:colon]

def check_format(full_name):
    for prefix in assignment_prefixes:
        plen = len(prefix)
        if re.match(prefix, full_name):
            return True
    return False

# Objects for deadline and submission info
assignment_list = []
assignment_names = []
maxes = {} # assignment IDs are the keys
ids_to_snums = {}
ids_to_names = {}
names_to_snums = {}
late_days = defaultdict(lambda: 0) # keys are student IDs

submission_statuses = defaultdict(lambda: defaultdict(lambda: -1)) # student ID are the keys, linked to dictionaries with assignment IDs as keys
records = defaultdict(lambda: []) # keys are studend IDs

# Settings from arguments
which_course = sys.argv[1]

print ("-> Finding course...")
course_id = find_course_id(which_course)

"""
print ("-> Finding sections...")
section_data = get_response("courses/{}/sections".format(course_id))
for s in section_data:
    section_list.append(s['id'])
print ("    {} section(s).".format(len(section_data)))
"""

print ("-> Finding students...")
people = get_response("courses/{}/students".format(course_id))
for p in people:
#    print("-> found {} {}, {}".format(p['id'], p['sortable_name'], p['sis_user_id']))
    ids_to_snums[p['id']] = p['sis_user_id']
    names_to_snums[p['sortable_name']] = p['sis_user_id']
    ids_to_names[p['id']] = p['sortable_name']
print ("-> Total students: {}".format(len(ids_to_snums)))

print ("-> Finding assignments...")
all = get_response("courses/{}/assignments".format(course_id))
for assignment in all:
    if check_format(assignment['name']):
        if assignment['published'] == False:
            # skip assignments that aren't published
            continue
        assignment_list.append(assignment['id'])
        assignment_names.append(assignment['name'])
        maxes[assignment['id']] = assignment['points_possible']
print ("-> Total: {} assignments.".format(len(assignment_list)))
print()

for (i, assignment_id) in enumerate(assignment_list):
    print ("-> Processing", assignment_names[i])
    submissions = get_response("courses/{}/assignments/{}/submissions".format(course_id, assignment_id))
    for s in submissions:
        snum = ids_to_snums[s['user_id']]
        sname = ids_to_names[s['user_id']]
        score = s['score']
        if not (s['missing'] or s['excused']):
            status = 0
            hrs = s['seconds_late'] / (3600) - GRACE_PERIOD / 60.0
            days = math.ceil(hrs / 24.0)
            if days > 0:
#                print("***", days, s['late_policy_status'], s['submitted_at'])
                status = math.ceil(days)
                late_days[snum] += status
                records[snum].append((maxes[assignment_id], score, i, days))
            submission_statuses[snum][assignment_id] = status
        else:
            submission_statuses[snum][assignment_id] = -1
print()

for (id, name) in ids_to_names.items():
    snum = ids_to_snums[id]
    if not snum:   # "Test Student" has an snum of None
        continue
    print("-----------------------")
    print(name)
    print("-----------------------")
    if snum not in records:
        print("No late assignments")
    else:
        rec = records[snum]
        rec.sort()
        rec.reverse()
        for (outof, score, i, days) in rec:
            assn = assignment_names[i]
            print(short_name(assn))
            print("Score: {:.1f} / {:.0f}".format(score, outof))
            print("Late: {:.0f} day{}".format(days, "s" if days>1 else ""))
            print()
    print()
        




"""
for name in sorted(names_to_snums.keys()):
    snum = names_to_snums[name]
    print (name)
    tot_days = late_days[snum]
    print ("{} day{} total".format(tot_days, "" if tot_days==1 else "s"))
    for (k, assignment_id) in enumerate(assignment_list):
        assignment_name = assignment_names[k]
        days = submission_statuses[snum][assignment_id]
        status = "on time"
        if days == -1:
            status = "missing (or excused)"
        if days > 0:
            status = "late, {} day{}".format(days, "" if days==1 else "s")
        print ("  {}: {}".format(short_name(assignment_name), status))
    print()
"""

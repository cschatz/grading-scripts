#!/usr/bin/env python3

from canvas import *
from scinet_config import *
# import MySQLdb
import pymysql
import argparse, sys, json, glob, re, os

# "globals" for live practice status
LP_MSGS = ["No answer / late answer", "No answer / late answer", "Incorrect answer", "Correct answer"]

# Set up arg parsing
parser = argparse.ArgumentParser()
parser.add_argument("sncourse", help="SciNet coursename")
parser.add_argument("cvcourse", help="Canvas coursename")
parser.add_argument("section", help="Section name")
args = parser.parse_args()
             
assignment_name = "In-Class Participation"
if args.section != "":
    assignment_name += " " + args.section

course_id = find_course_id(args.cvcourse)
scinet_course = args.sncourse
assignment_id, _ = find_assignment_id(course_id, assignment_name, True)
assignment_group_id = find_assignment_group_id(course_id, "Participation")
if assignment_group_id == 0:
    raise Exception("Can't find assignment group ID")
section_id = None
if args.section != "":
    section_id = find_section_id(course_id, args.section)

print ("> Got course and group IDs")
print ()

if assignment_id != 0:
    print ("> Participation assignment exists - deleting")
    result = do_request("delete", "courses/{}/assignments/{}".format(course_id, assignment_id))
    print (">  Deleted")
    print ()

print ("> Creating blank participation assignment")
payload = {}

payload["assignment[name]"] = assignment_name
payload["assignment[assignment_group_id]"] = assignment_group_id
payload["assignment[published]"] = True
payload["assignment[notify_of_update]"] = False
if section_id != None:
    payload["assignment[only_visible_to_overrides]"] = True
result = do_request("post", "courses/{}/assignments".format(course_id), payload)
if 'id' in result:
    assignment_id = result['id']
    print (">  Created - ID: {}".format(assignment_id))
    print ()
    if section_id != None:
        print ("> Setting override for section")
        payload = {}
        payload["assignment_override[course_section_id]"] = section_id
        result = do_request("post", "courses/{}/assignments/{}/overrides".format(course_id, assignment_id), payload)
        print (">  Override set")

else:
        raise Exception("Failed to create participation assignment")



date = None
records = {}
scores = {}
canvas_ids = {}
names = {}

try:
    db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PW, db=MYSQL_DB)
    cursor = db.cursor()

    cursor.execute("SELECT whenstart from starts WHERE course='{}' and section='{}'".format(args.sncourse, args.section))
    result = cursor.fetchone()
    if result == None:
        raise Exception("Could not determine start time")

    coursestart = result[0]

    print("> Class start time is ", coursestart)
    print()

    cursor.execute("SELECT day from attendance WHERE course='{}' and section='{}' GROUP BY day ORDER BY day".format(args.sncourse, args.section))
    results = cursor.fetchall()
    # flatten
    days = [val for sublist in results for val in sublist]

    print("> Collecting attendance data")
    for day in days:
        print (">  {}".format(str(day)))
        # select all IDs on all available days, with NULLs for absences
        cursor.execute("SELECT ID, lname, fname, canvas_id, whenhere, time_to_sec(timediff(whenhere, '{0}')) FROM (select * from attendance WHERE day='{1}' AND course='{2}') aa RIGHT OUTER JOIN (select ID, lname, fname, canvas_id from roster WHERE course='{2}' and section='{3}' and ID>1) rr using (ID) ORDER BY lname, fname".format(coursestart, day, args.sncourse, args.section))   
        results = cursor.fetchall()
        for row in results:
            sn_id = row[0]
            lname = row[1]
            fname = row[2]
            canvas_id = row[3]
            arrival = row[4]
            delta = row[5]
            status_note = ""
            points = 0
            names[sn_id] = "{} {}".format(lname, fname)
            # print sn_id, lname, fname,
            if sn_id not in records:
                records[sn_id] = []
            if sn_id not in scores:
                scores[sn_id] = 0
            if arrival == None:
                status_note = "Absent (0 points)".format(day)
            else:
                minutes = int(round(delta/60.0))
                # print "   {} ({})".format(arrival, minutes)
                if minutes <= 7:
                    status_note = "On time at {} (5 points)".format(arrival)
                    points = 5
                elif minutes < 17:
                    status_note = "Somewhat late at {} (3 points)".format(arrival)
                    points = 3
                else:
                    status_note = "Late at {} (0 points)".format(arrival)
            
            records[sn_id].append("Attendance {}: {}".format(day, status_note))
            canvas_ids[sn_id] = canvas_id            
            scores[sn_id] += points

    print("> Attendance done")
    print()
    """
    LIVE PRACTICE accounting
    """

    print("> Collecting live practice data")
    cursor.execute("SELECT ID, date(answerwhen) as dd, score FROM daily where course='{0}' and section='{1}' and ID in (select ID from roster where course='{0}' and section='{1}') order by dd".format(args.sncourse, args.section))
    results = cursor.fetchall()
    for row in results:
        sn_id = row[0]
        day = row[1]
        rating = row[2]
        if sn_id not in records:
            records[sn_id] = []
            
        # map -1,0,1,2 -> 0,2,2
        points = (rating + 1) // 2 * 2

        status_note = "{} ({} points)".format(LP_MSGS[rating+1], points)
        records[sn_id].append("Live practice {}: {}".format(day, status_note))
            
        if sn_id not in scores:
            scores[sn_id] = 0
        else:
            scores[sn_id] += points

except Exception as e:
    print ("Error", e)
    sys.exit(1)
    
finally:    
    if db:
        db.close()
        

#    score_payload = {}
score_records = {}
comment_records = {}
for r in records:
    k = canvas_ids[r]
    # print r, canvas_ids[r], names[r], scores[r]
    print (scores[r], "  ", names[r])
    # print records[r]
    for entry in records[r]:
        print (" ", entry)
    comments = "\n".join(records[r])
    score_records[k] = str(scores[r])
    comment_records[k] = comments
#        score_payload["grade_data[{}][posted_grade]".format(k)] = str(scores[r])
#        score_payload["grade_data[{}][text_comment]".format(k)] = comments
    print ()
 
max_score = max(scores.values())
print ("> Live practice done")
print ()
print ("> Max PPs =", max(scores.values()))
print ()

print ("> Pushing maximum score to server")
assignment_payload = {}
assignment_payload["assignment[points_possible]"] = max_score
result = do_request("put", "courses/{}/assignments/{}".format(course_id, assignment_id), assignment_payload)
print ("> Done ")
print ()
    
print ("> Pushing grades and comments...")
for k in score_records:
    print (">  ", k)
    payload = {}
    payload["comment[text_comment]"] = comment_records[k]
    payload["submission[posted_grade]"] = score_records[k]
    result = do_request("put", "courses/{}/assignments/{}/submissions/{}".format(course_id, assignment_id, k), payload)
    #print (">  ", result['workflow_state'])
print ("> Done")
    



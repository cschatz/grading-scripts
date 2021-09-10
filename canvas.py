import requests

CANVAS_TOKEN='FAKE TOKEN - replace with API access token from Canvas';
AUTH_HEADER = {'Authorization': 'Bearer ' + CANVAS_TOKEN}
API_BASE = 'https://canvas.instructure.com/api/v1/'
MAX_RESULTS = 200 # make sure we get everything in one "page"
COLLEGE_CONSTANT = 136320000000000000 # subtract this from all ID numbers in canvas to get actual IDs

def get_response(endpoint):
    """
    Generic function to get JSON response from Canvas
    """
    r = requests.get(API_BASE + endpoint + "?per_page={}".format(MAX_RESULTS),  headers=AUTH_HEADER)
    return r.json()

def do_request(req_type, endpoint, post_params=None):
    """
    Same as above, but for PUT/POST/DELETE requests
    """
    r = None
    if req_type == "put":
        r = requests.put(API_BASE + endpoint, headers=AUTH_HEADER, data=post_params)
    elif req_type == "post":
        r = requests.post(API_BASE + endpoint, headers=AUTH_HEADER, data=post_params)        
    elif req_type == "delete":
        r = requests.delete(API_BASE + endpoint, headers=AUTH_HEADER, data=post_params)        
    else:
        raise Exception("Unknown request type '" + req_type + "'")
    return r.json()


def find_course_id(course_code):
    all = get_response("courses")
    for item in all:
        if item['workflow_state'] == 'available' and item['course_code'].lower() == course_code.lower():
            return item['id']
    raise Exception("Unable to find course code '" + course_code + "'")

def find_assignment_id(course_id, assignment_name, missing_ok=False):
    """
    Searches for the given assignment, returning a tuple
    containing the assignment ID and the maximum score
    """
    all = get_response("courses/{}/assignments".format(course_id))
    n = len(assignment_name)
    for item in all:
        if item['name'][0:n].lower() == assignment_name[0:n].lower():
            return (item['id'], item['points_possible'])
    if missing_ok:
        return (0, 0)
    else:
        raise Exception("Unable to find assignment name '" + assignment_name + "'")

def find_assignment_group_id(course_id, group_name):
    all = get_response("courses/{}/assignment_groups".format(course_id))
    for item in all:
        if item['name'].lower().find(group_name.lower()) == 0:
            return item['id']
    raise Exception("Unable to find assignment group '" + group_name + "'")

def find_section_id(course_id, section_name):
    all = get_response("courses/{}/sections".format(course_id))
    if section_name == "":
        if len(all) != 1:
            raise Exception("Course has multiple sections, cannot use empty-string section name")
        return all[0]['id']
    for item in all:
        if item['name'].lower().find(section_name.lower()) == 0:
            return item['id']
    if len(all) == 1:
        print ("WARNING: Single-section course, but you gave a section name")
    raise Exception("Unable to find section name '" + section_name + "'")

def convert_id(sis_id, institution):
    if institution == "Mills":
        return int(sis_id[1:]) # strip leading letter
    else:
        raise Exception("Don't know how to convert IDs for institution " + institution)

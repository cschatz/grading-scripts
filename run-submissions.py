#!/usr/bin/env python
import sys, glob, os, re, subprocess
from utils import *

CANVAS_PATTERN = '(((\w|-)+)_(\d+)_(\d+)_(.+))'
CANVAS_PERL_REPLACEMENT = 's/[^_]+?_\d+?_\d+?_//' # eliminate canvas numbers from filename
GENERAL_PERL_REPLACEMENT = 's/^[^\\*]+\\///' # strip leading path components

EDITOR = "emacs"
INTERPRETERS = { 'py': 'python', 'rb': 'ruby', 'sh': 'bash', 'js': 'node' }
KNOWN_TYPES = [ "cpp", "swift", "zip", "ios" ]

GRADING_DIR = "/Users/cschatz/thumper/grading"

skip_commented = False
regrades_only = False

def between_submissions():
    for i in range(5):
        print

def get_standard_choice(default):
    c = get_choice(["run", "rebuild", "good", "unzip", "edit", "comment", "comment/output", "both", "purerun", "done"], ["r", "rr", "g", "z", "e", "c", "cc", "ec", "p", "d"], default)
    next = ""
    if c in ["r", "rr", "e", "p"]:
        next = "c"
    else:
        next = "d"
    return next, c


def fail(msg):
    print
    print "*** FAIL:", msg
    print
    sys.exit(-1)


def is_script(name, extension):
    return extension in INTERPRETERS.keys()


def run_script(name, extension):
    os.system("{} '{}.{}'".format(INTERPRETERS[extension], name, extension)) 


def program_exists(name, extension, sub_type):
    # If this is Python/etc, program exists if source code exists
    if is_script(name, extension):
        True
    elif sub_type == "ios":
       return os.path.isdir(name + ".dir")
    else:
        return os.path.isfile(name + ".prog")

        
def comment_submission(name, extension, also_edit, copy_output):
    if not also_edit:
        if copy_output:
            os.system("echo \"\n\n\n=====\n\" > '{}.comments'".format(name)) 
            os.system("cat .output >> '{}.comments'".format(name))
        os.system("{} '{}.comments'".format(EDITOR, name))
    else:
        os.system("{0} '{1}.comments' '{1}.{2}'".format(EDITOR, name, extension))

def edit_submission(name, extension):
    if extension == "zip":
        extension = "dir"
    os.system("{} {}.{}".format(EDITOR, name, extension))


def mark_good(name):
    os.system("echo 'Good.' > {}.comments".format(name))


def build_with_makefile(name):
    if not os.path.isfile("Makefile"):
        print "-> WARNING: No Makefile present in the outer submission directory"
        return False
    print "-> Using Makefile (stem = {})".format(name)
    os.environ["STUDENT_CPP"] = "{}.cpp".format(name)
    os.environ["STUDENT_EXEC"] = "{}.prog".format(name)
    os.environ["STUDENT_SRCDIR"] = "{}.dir".format(name)
    os.environ["STUDENT_SWIFT"] = "{}.swift".format(name)
    os.system("rm '{}.prog'".format(name))
    exit_val = os.system("make &> .errors")
    return (exit_val == 0)


def build_cpp(name):
    exit_val = 0
    if os.path.isfile("Makefile"):
        return build_with_makefile(name)
    else:
        # Use "plain" compiling of a single .cpp file
        print "-> Using g++ -std=c++14 -o _.prog _.cpp"
        exit_val = os.system("g++ -std=c++14 -o '{}.prog' '{}.cpp' &> .errors".format(name, name))
        return (exit_val == 0)

def build_swift(name):
    exit_val = 0
    if os.path.isfile("Makefile"):
        return build_with_makefile(name)
    else:
        print "-> Using swiftc -o _.prog _.swift"
        exit_val = os.system("swiftc -o {}.prog {}.swift &> .errors".format(name, name))
        return (exit_val == 0)

def expand_zip(name, keep_structure=False):
    EXCLUSIONS = "*._* __* *.DS_Store"
    src_dir = '{}.dir'.format(name)
    if not os.path.isdir(src_dir):
        print "-> Not unzipped yet"
        print "-> Creating source directory"
        os.system("mkdir '{}'".format(src_dir))
        print "-> Unzipping"
        if keep_structure:
            os.system("unzip -o -d '{}' '{}.zip' -x {}".format(src_dir, name, EXCLUSIONS))
        else:
            os.system("unzip -jo -d '{}' '{}.zip' -x {}".format(src_dir, name, EXCLUSIONS))
    else:
        print "-> Already unzipped"

def build_zip(name):
    """
    Build a submission in the form of a .zip file
    This REQUIRES the outer submission directory to have a Makefile available
    """
    expand_zip(name)
    return build_with_makefile(name)
    

def build_ios(name):
    """
    'Building' an iOS submission really just means unzipping the
    Xcode project.
    """
    expand_zip(name, keep_structure=True)
    return True

def run_ios(name):
    print "Running iOS project {}".format(name)
    project_file = subprocess.check_output(["find", "{}.dir".format(name), "-name", "*.xcodeproj", "-a", "-not", "-path", "*__MACOSX*"]).strip()
    print "> open \"{}\"".format(project_file)
    os.system("open \"{}\"".format(project_file))

def build_submission(name, extension, sub_type):
    # print "***** {}".format(name)
    if is_script(name, extension):
        print "-> Submission is an interpreted language, no need to build"
        return True
    if sub_type == "ios":
        return build_ios(name)
    elif extension == "cpp":
        return build_cpp(name)
    elif extension == "zip":
        return build_zip(name)
    elif extension == "swift":
        return build_swift(name)
    else:
        fail("Internal error, build_submission() has no mechanism to handle {} files".format(extension))


def handle_errors(name):
	see_errs = get_brief_choice("See error output", ["y", "n"], "y");
	if see_errs == "y":
		os.system("cat .errors")
	echo_errs = get_brief_choice("Copy errors to comments", ["y", "n"], "y");
	if echo_errs == "y":
		os.system("echo 'This submission could not be compiled.' > '{}.comments'".format(name)) 
		os.system("echo >> '{}.comments'".format(name))
		os.system("echo '=====' >> '{}.comments'".format(name))
		os.system("cat .errors >> '{}.comments'".format(name))
		os.system("perl -p -i -e '{}' '{}.comments'".format(GENERAL_PERL_REPLACEMENT, name))


def run_submission(name, extension, sub_type, force_rebuild, skip_expect_script):
	ready_to_run = True
	if force_rebuild or not program_exists(name, extension, sub_type):
		ready_to_run = (build_submission(name, extension, sub_type))
	if not ready_to_run:
		print "-> Submission is NOT ready to run due to errors"
		handle_errors(name)
	else:
		print "-> Submission is ready to run"
		if is_script(name, extension):
			print "-> Running submission (with interpreter)"
			run_script(name, extension)
		else:
			print "-> Running submission"
			if os.path.isfile("RUN_COMMAND"):
				os.environ["STUDENT_CPP"] = "{}.cpp".format(name)
				os.environ["STUDENT_EXEC"] = "{}.prog".format(name)
				os.environ["STUDENT_SRCDIR"] = "{}.dir".format(name)
				os.system("./RUN_COMMAND")
			elif not skip_expect_script and os.path.isfile("EXPECT"):
				os.system("expect -f ./EXPECT './{}.prog'".format(name))
			elif sub_type == "ios":
				run_ios(name)
			elif not skip_expect_script and os.path.isfile("INPUTS"):
				os.system("./{}.prog < INPUTS | tee .output".format(name))
			else:
                            if sub_type != "swift":
				os.system("./{}.prog | tee .output".format(name))
                            else:
				os.system("./{}.prog".format(name))

def process_one_submission(name, extension, sub_type):
    name = name.replace("'", "\\'")
    name = name.replace(" ", "\\ ")
    current_default = "r"
    while True:
        print
        current_default, choice = get_standard_choice(current_default)
        if choice == "e":
            edit_submission(name, extension)
        elif choice in ("r", "rr", "p"):
            run_submission(name, extension, sub_type, (choice == "rr"), (choice == "p"))
        elif choice == "c":
            comment_submission(name, extension, False, False)
        elif choice == "ec":
            comment_submission(name, extension, True, False)
        elif choice == "cc":
            comment_submission(name, extension, False, True)
        elif choice == "g":
            mark_good(name)
            print "-> Ok, marked this submission as good"
        elif choice == "z":
            if extension != "zip":
                print "*** Only applicable for .zip submissions"
            else:
                expand_zip(name)
        elif choice == "d":
            print "-> Ok, done with this submission"
            return


def process_file(filename, ext, sub_type):
        # Figure out filename stem and validity-check its name
        m = re.match(CANVAS_PATTERN + "." + ext, filename)
        if not m:
            print "*** ERROR - mismatch to standard filename pattern: " + filename
            sys.exit(-1)
        stem = m.group(1)
        anon = m.group(4) + m.group(5)

        # If we are skipping commented submissions, do that
        if skip_commented and os.path.isfile(stem + ".comments"):
            print "-> Skipping, already has comments"
            return

        # Process one submission
        print "===== {} =====".format(anon)
        process_one_submission(stem, ext, sub_type)    


def process_all():
    # Process arguments
    global skip_commented 
    global regrades_only
    if (len(sys.argv) < 4):
        print "Args: course assignment type [-s | -r]"
        sys.exit()
    if len(sys.argv) >= 5:
        if sys.argv[4] == "-s":
            print "Skipping submissions with comments"
            skip_commented = True
        elif sys.argv[4] == "-r":
            print "Processing regrades only..."
            regrades_only = True
        else:
            print "Unknown option '{}'".format(sys.argv[4])
            sys.exit()

    course, assignment, submission_type = sys.argv[1:4]

    # Can we handle the given extension?
    if not (submission_type in KNOWN_TYPES or ext in INTERPRETERS.keys()):
        fail("'{}' is not a recognized submissions type".format(ext))
        
    ext = submission_type if submission_type != "ios" else "zip"

    # Change directory to the right place
    subs_dir = "{}/{}/{}".format(GRADING_DIR, course, assignment)
    if not os.path.isdir(subs_dir):
        fail("No submit directory for course {} assignment {}".format(course, assignment))
    os.chdir(subs_dir)

    print "Checking for *." + ext
    # Loop through files
    files = glob.glob("*." + ext)
    for filename in files:
        # Visual space between submissions
        between_submissions()

        # Rename file if it contains spaces or parentheses
        newfilename = filename.replace(" ", "_")
        newfilename = newfilename.replace("(", "")
        newfilename = newfilename.replace(")", "")
        if newfilename != filename:
            os.system("mv '{}' '{}'".format(filename, newfilename))
            filename = newfilename
        
        # Report progress
        count = len(glob.glob("*.comments"))
        print "{} / {} ({:.1f}% left)".format(count, len(files), 100*(1-1.0*count/len(files)))

        # Process the current file
        process_file(filename, ext, submission_type)

if __name__ == "__main__":
    process_all()


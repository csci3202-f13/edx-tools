#!/usr/bin/python
# -*- coding: utf-8 -*-
"""submission.py: scrape student assignment submission data from edX and process it

%InsertOptionParserUsage%

Requirements:
 requests module, at least version ?? (something beyond what is in Ubuntu precise)

Example - show debugging output:
 submission.py -d 10 -p 2efc16e499f243298673515be21fc1ec -s janedoe34

Example - get late grades with slips:
 submission.py -p d9bf5571dcbd4d24b117d78c31630f37 -t 2013-9-30-23:00 -l

Example - write output csv to test.csv instead of d9bf5571dcbd4d24b117d78c31630f37_grades.csv
 submission.py -p d9bf5571dcbd4d24b117d78c31630f37 -f test.csv

Example - summarize student clicker submissions for a problem.  Add "-o" to also output per-student submissions
 submission.py -c -p 2a20ae2aa9dd45449ab19b550f36c372

"""
from __future__ import division

import re
import logging
import json
from optparse import OptionParser
import requests
import datetime as dt
from BeautifulSoup import BeautifulSoup
import config
from collections import Counter
from os.path import expanduser

__version__ = "0.2.0"
__copyright__ = "Copyright (c) 2013 Aaron Davis, Neal McBurnett"
__license__ = "GPL v3"

parser = OptionParser(prog="submission.py", version=__version__)

def one_or_more_options(option, opt_str, value, parser):
    """Implement one-or-more values for an argument in OptionParser.

    Until we move to argparse which has clean native support for nargs="*"....
    """
    args = []
    for arg in parser.rargs:
        if arg[0] != "-":
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)

parser = OptionParser()

parser.add_option("-d", "--debuglevel",
  type="int", default=logging.WARNING,
  help="Set logging level to debuglevel: DEBUG=10, INFO=20,\n WARNING=30 (the default), ERROR=40, CRITICAL=50")

parser.add_option("-o", "--output",
  action="store_true",
  help="Output the autograder results")

parser.add_option("-s", "--student",
  dest="students", action="callback", callback=one_or_more_options,
  help="Select a specific student by edX id.  May be specified multiple times.")

parser.add_option("-p", "--problem",
  dest="problems", action="callback", callback=one_or_more_options,
  help="Select a specific problem by edX id.  May be specified multiple times.")

parser.add_option("-l", "--late",
  dest="is_late", action="store_true",
  help="Supress output in the csv for those who didn't submit late: e.g. when viewing late submissions to s")

parser.add_option("-c", "--clicker",
  dest="is_clicker", action="store_true",
  help="Show student clicker submissions, save in clicker.csv")

parser.add_option("-t", "--duedate",
  dest="due_date", action="store", type="string",
  help="Date assignment was due. This is needed for late submissions to calculate slip days\n" +
       "Must be in UTC time, in the form Year-Month-Day-Hour:Minute, for example 2013-9-30-23:00.")

parser.add_option("-f", "--file",
  dest="filename", action="store", type="string",
  help="Name of output file.")

# incorporate OptionParser usage documentation in our docstring
__doc__ = __doc__.replace("%InsertOptionParserUsage%\n", parser.format_help())

num_date_pattern = re.compile("#([0-9]+): (.*)Score: (.*){")
bonus_pattern = re.compile("[^0-9.]*([0-9]+\.[0-9]+|[0-9]+).*")
math_pattern = re.compile("^[ 0-9\+\*-/\.\(\)\^]+$")

# read in values from config.py
courseserver = config.courseserver
coursepath = config.coursepath
course = config.course
name2sid = {k: v for k, v in zip(config.users.split(), config.sids.split())}

def get_cookies():
    """Read cookies file, copy-pasted from chrome debugger, and return in a form suitable for requests.get."""
    home = expanduser('~')
    with open(home + '/config/edx-tools/cookie.txt') as f:
        lines = f.readlines()
        lines = [line.strip(' \t\n\r') for line in lines if '✓' not in line]

        d = {}
        count = 0
        for line in lines:
            if count == 0:
                cookie_name = line
            if count == 1:
                cookie_val = line
                d[cookie_name] = cookie_val
            if count == 5:
                count = 0
            else:
                count += 1
    return d

def unescape(s):
    """minimal html unescape function for quotes, <, >, and &."""
    s = s.replace("&amp;", "&")
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&#34;", '"')
    s = s.replace("&#39;", "'")
    return s

def parse(content):
    """Return all submissions as list of dictionaries."""
    soup = BeautifulSoup(content)
    submissions = soup.findAll('div')

    submission_data = []
    for s in submissions:
        t = s.getText()
        try:
            num, date, score = num_date_pattern.findall(t)[0]
            num = s.find('b').getText()
            data = json.loads(unescape(s.find('pre').getText()))
            d = {'submission_num': num,
             'date': date,
             'score': score,
             'detail': data}
            submission_data.append(d)
        except Exception, e:
            logging.error("Error finding num_date_pattern: %s.  Text:\n%s" % (e, t))
    return submission_data

def get_submissions(username, problem, cookies, is_clicker, sesssion):
    """Fetch submission history url and parse output into dictionary."""
    url = '/'.join([courseserver, coursepath, course, 'submission_history', username, 'i4x:/', coursepath, 'problem', problem])
    user_agent = {'User-agent': 'csci3202-f13/edx-tools/progress ' + requests.utils.default_user_agent()}
    r = sesssion.get(url, cookies=cookies, headers=user_agent)
    content = r.text
    print 'getting data for ' + username
    return parse(content)

def get_bonus(autograder_out):
    """Print bonus info to std out."""
    lines = autograder_out.split('\n')
    bonus_lines = []
    bonus_start = None
    bonus_end = None
    for i, line in enumerate(lines):
        if 'Question extra' in line:
            bonus_start = i + 3
        if bonus_start and 'Extra credit threw a string exception' in line:
            return None
        if bonus_start and '</pre>' in line:
            bonus_end = i + 1
            break
    if bonus_start and bonus_end:
        bonus_lines = lines[bonus_start: bonus_end]
        print '---------------'
        for line in bonus_lines:
            print line.strip().replace('<pre>', '').replace('</pre>', '')
        print '---------------'

def get_score(submissions, problem, due_date, options):
    """Get the best score, and bonus score."""
    best_score = None
    best_percent = 0
    best_ts = None
    bonus = None
    partners = set()
    for i, s in enumerate(submissions):
        timestamp = s['date']
        submission_num = s['submission_num']
        detail = s['detail']
        if 'correct_map' in detail and not options.is_clicker:
            try:
                autograder_out = detail['correct_map']['i4x-BerkeleyX-CS188x-17-problem-' + problem + '_2_1']['msg']
            except Exception, e:
                logging.error("Error getting output: %s.  Submission:\n%s" % (e, s))
                continue

            autograder_out = unescape(autograder_out)
            if options.output:
                print("Autograder output for submission %s on %s:\n%s" % (submission_num, timestamp, autograder_out))

            get_bonus(autograder_out)
            extra = bonus_pattern.findall(autograder_out)
            if extra:
                bonus = extra[0]
        num, denom = s['score'].split(' / ')
        percent = float(num) / float(denom) if 'None' not in num else 0
        if percent > best_percent:
            best_score = s['score']
            best_percent = percent
            best_ts = timestamp
        if 'student_answers' in detail and not options.is_clicker:
            partner = detail['student_answers'].get('i4x-BerkeleyX-CS188x-17-problem-' + problem + '_3_1', '')
            if partner:
                partners.add(partner)
    logging.info("Partners: %s" % (partners))

    if best_ts is not None and due_date is not None:
        submitted = dt.datetime.strptime(best_ts.split('+')[0], '%Y-%m-%d %H:%M:%S')
        slip_days_used = str((submitted - due_date).days + 1)
    else:
        slip_days_used = 'N/A'
    return best_score, bonus, partners, slip_days_used

def get_clicker_results(submissions, results, options):
    """Get results from an edx question designed to be an in-class exercise.

    Results are printed in the terminal. For every answer given by any of the students,
    the number of students who gave that answer will be shown. The correct answer will
    be indicated too.
    """
    try:
        # get most recent submission for clicker
        answers = submissions[0]['detail']['student_answers']
        correct_map = submissions[0]['detail']['correct_map']
    except Exception, e:
        logging.info("Error getting clicker answers: %s." % e)
        return

    keys = sorted(answers.keys())
    if options.output:
        header = '{}{}{}{}'.format('problem'.ljust(10), 'evaluated'.ljust(12), 'entered'.ljust(25), 'correctness'.ljust(10))
        print header + '\n' + ('-' * len(header))

    for i, key in enumerate(keys):
        ans = answers[key]
        if type(ans) is not list:
            if math_pattern.match(ans):
                ans = ans.replace('^', '**')
                ans = str('%.4f' % eval(ans))
            else:
                ans = ans.lower()
        else:
            ans = 'MC: {}'.format(' '.join([a.split('_')[1] for a in ans]))

        try:
            is_correct = correct_map[key]['correctness']

            if key in results:
                results[key].append((ans, is_correct[0]))
            else:
                results[key] = [(ans, is_correct[0])]

            if options.output and answers[key] != '':
                print '{}{}{}{}'.format(str(i+1).ljust(10), ans.ljust(12), answers[key].ljust(25), is_correct.ljust(10))

        except Exception, e:
            logging.info("Error get correct map: %s." % e)
            print correct_map
    try:
        return submissions[0]['score']
    except:
        logging.info("Error getting clicker score: %s." % e)


def view_submission(problem, filename, users, options, cookies, due_date, late=False):
    results = {}
    if filename is None:
        if options.is_clicker:
            filename = 'clicker-{}.csv'.format(problem)
        else:
            filename = problem + '_grades.csv'
    with open(filename, 'w') as f:
        if options.is_clicker:
            f.write(','.join(['name', 'score']) + '\n')
        else:
            f.write(','.join(['sid', 'name', 'grade', 'bonus', 'partners', 'slips used']) + '\n')

        sesssion = requests.Session()
        for user in users:
            submissions = get_submissions(user, problem, cookies, options.is_clicker, sesssion)
            logging.debug("User: %s, %d submissions" % (user, len(submissions)))

            if options.is_clicker and len(submissions) > 0:
                score = get_clicker_results(submissions, results, options)
                if score is not None:
                    f.write(','.join([user, score]) + '\n')
                    if options.output:
                        print 'Score for {}:\t{}\n'.format(user, score)
            elif not options.is_clicker:
                score, bonus, partners, slips_used = get_score(submissions, problem, due_date, options)
                partner = '|'.join(partners)
                sid = name2sid.get(user, 'Not Found')
                if late and 'None' in str(score):
                    # don't write late scores unless they actually tried to submit late
                    pass
                else:
                    f.write(','.join([sid, user, str(score), str(bonus), partner, slips_used]) + '\n')

    if options.is_clicker:
        print '\nResults\n--------'
        keys = sorted([(int(key.split('_')[1]), key) for key in results.keys()])
        for i, (_, k) in enumerate(keys):
            c = Counter(results[k])
            print 'Problem {} ({}):'.format(str(i+1), k)
            print '\t{}{}{}'.format('answer'.ljust(12), 'num students'.ljust(15), 'correctness')
            for ans, num in c.items():
                correct = '(correct)' if ans[1] == 'c' else ''
                if ans[0] != '':
                    print '\t{}{}{}'.format(ans[0].ljust(12), str(num).ljust(15), correct)

def main(parser):
    "Parse  with given OptionParser arguments"
    (options, args) = parser.parse_args()

    #configure the root logger.  Without filename, default is StreamHandler with output to stderr. Default level is WARNING
    logging.basicConfig(level=options.debuglevel)   # ..., format='%(message)s', filename= "/file/to/log/to", filemode='w' )
    logging.debug("options: %s; args: %s", options, args)

    cookies = get_cookies()

    if options.filename:
        filename = options.filename
    else:
        filename = None

    if options.students:
        users = options.students
    else:
        users = config.users.split()

    if options.due_date:
        due_date = dt.datetime.strptime(options.due_date, '%Y-%m-%d-%H:%M')
    else:
        due_date = None

    for problem in options.problems:
        view_submission(problem, filename, users, options, cookies, due_date, options.is_late)

if __name__ == "__main__":
    main(parser)

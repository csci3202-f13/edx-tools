import os
import re
import simplejson
import time

from BeautifulSoup import BeautifulSoup

name_pattern = re.compile("'(.*)'")
email_pattern = re.compile("\((.*)\)")
ending_number_pattern = re.compile("\d+-(\d+)$")
# tooltips_pattern = re.compile("var detail_tooltips = ([^;]*);")
percent_score_pattern = re.compile("([0-9]+)%")
score_pattern = re.compile("([0-9]+) of ([0-9]+)")

def shorten_col_name(s):
    s = s.replace(' ', '')
    s = s.replace('Homework', 'H')
    s = s.replace('Project', 'P')
    s = s.replace('Lecture', 'L')
    s = s.replace('Midterm', 'M')
    s = s.replace(':PracticeTest', '_')
    return s

def _scores(progress_file, gather_keys=False):
    """Return a dictionary of values for the csv headers from html progress page.

    When gather_keys is true, also return a list of keys in the order they will appear
    in the csv. This is intended for just the first iteration.
    """

    pd = progress_file.read()

    # get name and email from html parse
    soup = BeautifulSoup(pd)
    user = soup.findAll('header')[1].getText()
    name = name_pattern.findall(user)[0]
    email = email_pattern.findall(user)[0]

    # intialize dict with values obtained so far
    d = {'Name': name, 'Email': email}

    # on the first run through, make a list of keys for maintaining the
    # same order when creating the csv
    if gather_keys:
        keys = ['Name', 'Email']
        problem_keys = []
        possible_points_list = ['Possible Points', 'N/A']
        prob_possible_points_list = []

    # the nodes with class "scores", and nearby sibling and parent nodes,
    # contain the score information we need
    scores = soup.findAll('section', {'class': 'scores'})
    for s in scores:
        sib = s.findPreviousSibling('h3')
        if sib:
            span = sib.findAll('span', {'class': 'sr'})
            if span:
                child_text = span[0].getText()
                parent_text = span[0].findParent().getText().replace(child_text, '')

                # practice scores and the math assessment scores are not collected
                # because they appeared to be inconsistent across different students,
                # and less useful
                if 'Math' not in parent_text:
                    points, possible = score_pattern.findall(child_text)[0]
                    if 'Midterm' not in parent_text:
                        key = parent_text.split(':')[0]
                        if 'practice' in parent_text or 'make-up' in parent_text:
                            key += 'L'
                    else:
                        key = parent_text
                    if 'continued' in parent_text:
                        key += '_2'
                    key = shorten_col_name(key)
                    d[key] = points
                    if gather_keys:
                        keys.append(key)
                        possible_points_list.append(possible)
                    problems = s.findAll('li')
                    for i, p in enumerate(problems):
                        problem_key = ''.join([key, 'p{}'.format(i + 1)])
                        points, possible = p.getText().split('/')
                        problem_key = shorten_col_name(problem_key)
                        d[problem_key] = points
                        if gather_keys:
                            problem_keys.append(problem_key)
                            prob_possible_points_list.append(possible)
    if gather_keys:
        keys += problem_keys
        possible_points_list += prob_possible_points_list
        return d, keys, possible_points_list
    else:
        return d

def _write_csv(lines, headers, possible_points, dest_dir=None):
    """Write a csv file named csv-<timestamp>.

    Args:
        lines: A list of dictionaries where keys are the header values for
            the csv.
        headers: a list of headers for the csv in the order they will appear
        possible_points: a list of max possible points for each header
        dest_dir: optional destination dir. The directory must already exist.
            If not given, the file will be written to the current directory.

    """
    ts = time.strftime('%Y%m%dT%H%M%S', time.localtime())
    if dest_dir:
        dest = os.path.join(os.getcwd(), dest_dir)
        if not os.path.isdir(dest):
            os.mkdir(dest_dir)
        csv_name = os.path.abspath('{}/csv-{}.csv'.format(dest_dir, ts))
        print 'writing csv file {}'.format(csv_name)
    else:
        csv_name = 'csv-{}.csv'.format(ts)
        print 'writing csv file {} to {}'.format(csv_name, os.getcwd())
    with open(csv_name, 'w') as f:
        f.write(','.join(headers) + '\n')

        # uncomment the next line to have the second row be the possible points for each category
        # f.write(','.join(possible_points) + '\n')
        for line_dict in lines:
            f.write(','.join([line_dict[header] if header in line_dict else 'Not Found' for header in headers]) + '\n')
    if dest_dir:
        return csv_name
    else:
        return os.path.join(os.getcwd(), csv_name)

def write_progress_csv(src_dir, dest_dir=None, verbose=False):
    """Write a csv file named csv-<timestamp>.

    Args:
        src_dir: The directory where the scraped progress report html docs are.
        dest_dir: optional destination to write the csv file to. If not given,
            the file will be written to the current directory. The directory
            must already exist.

    """
    lines = []
    gather_keys = True
    for root, dirs, files in os.walk(src_dir):
        for name in files:
            if name.startswith('.'):
                # don't look at hidden files, in particular .DS_Store on Mac
                continue
            if verbose:
                print 'reading file {}'.format(name)
            progress_file = open(os.path.join(root, name))
            if gather_keys:
                line, keys, possible_points = _scores(progress_file, gather_keys)
                gather_keys = False
            else:
                line = _scores(progress_file)
            lines.append(line)
    csv = _write_csv(lines, keys, possible_points, dest_dir)
    if verbose:
        print 'finished!'
    return csv

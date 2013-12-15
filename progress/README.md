# Gather data on student progress by scraping edX course site as an instructor

Requirements

This was developed on Ubuntu Precise 12.04
Install these packages: python-simplejson ca-certificates python-beautifulsoup
  and ipython-notebook version 0.13 (from backports) via e.g. these commands for Ubuntu Precise 12.04:

    sudo apt-get -t precise-backports install ipython ipython-notebook ipython-qtconsole
    sudo apt-get install python-beautifulsoup python-simplejson ca-certificates

In order to run curl securely, you will need a certificate bundle. On OSX, you may need to
add this manually because the Apple version of curl doesn't ship with the CA cert bundle.
See this link for details: http://curl.haxx.se/docs/caextract.html. One way to
get the bundle on OSX is to download the .pem file from <a href="http://curl.haxx.se/docs/caextract.html">here</a>
and set the environment variable CURL_CA_BUNDLE to the path to this file.

Usage

* First set up your course config file in ~/config/edx-tools/config  using supplied template
* Run `edx-dump`
* Run `ipython notebook --pylab=inline edx-report.ipynb` to analyze data with ipython notebook

Sample results are in the tests directory.


# submission.py: View results for individual submissions

This script uses the requests module to get json data from edx for student submissions.

## Additional requirements

python-requests

## Setup

Fill in the following fields in config.py. Examples are shown in the file. Make sure that the same order is used in every list, so that the usernames, userids, sids, and emails all refer to the same student for every list index.

* users: edx user names in space separated string
* userids: edx user ids in space separated string
* sids: university student ids in space separated string
* emails: edx / university email in space separated string
* courseserver: "https://edge.edx.org/courses"
* coursepath = [School Name]/[Course Name]
* course = [Course year]

You will need your edx cookies again. Create a text file in the ~/config/edx-tools/config directory called cookies.txt. Open up the chrome debugger and copy/paste your edx cookies directly into that file. No other changes are needed, submission.py will parse the cookies for you.

## Usage

In edx, every problem that accepts submissions has an associated hex string as an identifier.
To use submission.py to get all student submissions for a given problem, use:

```
python submission.py -p [problem hash]
```

The intended use case is for problem submissions. The output will be csv with columns for student id, edx name, grade, bonus points recieved, partner, and optionally day passes since due date.

The output file will be called [problem hash]_grades.csv. To give it another name use -f [name]:

```
python submission.py -p [problem] -f [output file name]
```

To get days past due date, use -t [due date]. The due date must be in the form [year]-[month]-[day]-[hour]:[mintue], as in 2013-9-25-17:00. Enter due dates in UTC to be consistent with edx.

submission.py can also be used to moderate in-class "clicker" questions. Use the -c option if you want to get data from an in-class problem you have posted on the fly. If you want individual output for each student, use -o as well. This will print problem scores to the terminal, as well as writing a csv with student grades, called clicker_grades-[problem].csv by default.

####Examples:

Get data and days late for a project due on 2013-1-1 at noon, UTC. Save to my_output.csv
```
python submission.py -p 418746ead12 -f my_output.csv -l -t 2013-1-1-12:00
```

Get data and view output for an in-class problem:

```
python submission.py -p ae8726976b2 -c -o
```

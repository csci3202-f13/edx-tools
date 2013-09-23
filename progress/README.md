# Gather data on student progress by scraping edX course site as an instructor

Requirements

This was developed on Ubuntu Precise 12.04
Install these packages: python-simplejson ca-certificates python-beautifulsoup
  and ipython-notebook version 0.13 (from backports) via e.g. these commands for Ubuntu Precise 12.04:

    sudo apt-get -t precise-backports install ipython ipython-notebook ipython-qtconsole
    sudo apt-get install python-beautifulsoup python-simplejson ca-certificates

Usage

* First set up your course config file in ~/config/edx-tools/config  using supplied template
* Run `edx-dump`
* Run `ipython notebook --pylab=inline edx-report.ipynb` to analyze data with ipython notebook

Sample results are in the tests directory.

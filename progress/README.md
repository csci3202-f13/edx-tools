# Gather data on student progress by scraping edX course site as an instructor

Requirements

This was developed on Ubuntu Precise 12.04, with ipython 0.13 from backports.

Usage

* First set up your course config file in ~/config/edx-tools/config  using supplied template
* Run `edx-dump`
* Run `ipython notebook --pylab=inline edx-report.ipynb` to analyze data with ipython notebook

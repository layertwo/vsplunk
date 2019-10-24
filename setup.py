#!/usr/bin/env python3
from setuptools import setup

from vsplunk import vsplunk

setup(name='vsplunk',
      version=vsplunk.__version__,
      install_requires=['splunk-sdk>=1.6.11',
                        'visidata>=1.5.2'],
      description='Splunk App for Visidata',
      author=vsplunk.__author__,
      url='https://www.github.com/layertwo/vsplunk',
      python_requires='>=3.6',
      scripts=['bin/vsplunk'],
      packages=['vsplunk'],
      license='GPLv3',
      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: Log Analysis',
        'Topic :: Security'
      ],
      keywords=('splunk tabular data spreadsheet terminal curses visidata'))

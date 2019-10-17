#!/usr/bin/env python3
from setuptools import setup

from vsplunk import vsplunk

setup(name='vsplunk',
      version=vsplunk.__version__,
      install_requires=['splunk-sdk', 'visidata'],
      dependency_links=['git+ssh://github.com/saulpw/visidata@v2.-1'],
      description='Splunk App for Visidata',
      author=vsplunk.__author__,
      python_requires='>=3.6',
      scripts=['bin/vsplunk'],
      packages=['vsplunk'],
      license='GPLv3')

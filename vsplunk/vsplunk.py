#!/usr/bin/env python3
import argparse
import configparser
import os
from pathlib import Path

from visidata import asyncthread, ColumnItem, Sheet, deduceType, status, run

__version__ = 0.1
__author__ = 'Lucas Messenger'

def get_args():
    """
    get args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=os.path.join(Path.home(), '.vsplunk'))
    return parser.parse_args()


def read_config(path):
    """
    read ~/.vsplunk for splunk settings
    """
    config = configparser.ConfigParser()
    config.read(path)

    if 'SPLUNK' in config.sections():
        return config['SPLUNK']
    config['SPLUNK'] = {'host': 'localhost',
                        'port': 8089,
                        'scheme': 'https',
                        'username': 'admin',
                        'password': 'changeme'}

    with open(path, 'w') as fp:
        config.write(fp)
    return read_config(path)


class SplunkSheet(Sheet):
    def __init__(self, name, **kwargs):
        self.colnames = {}
        super().__init__(name, **kwargs)
        try:
            import splunklib.client
            self.client = splunklib.client.connect(**kwargs)
            status('connected to splunk', priority=2)
        except Exception as e:
            status(e, priority=3)

    def addRow(self, row, index=None):
        super().addRow(row, index=index)
        if isinstance(row, dict):
            for k in row:
                if k not in self.colnames:
                    if k.startswith('_'):
                        c = ColumnItem(k, type=deduceType(row[k]), width=0)
                    else:
                        c = ColumnItem(k, type=deduceType(row[k]))
                    self.colnames[k] = c
                    self.addColumn(c)
            return row

    @asyncthread
    def runQuery(self, query):
        """
        add rows from query results
        """
        # clear the board on new query
        self.colnames = {}
        self.rows.clear()
        self.columns.clear()
        [self.addRow(r) for r in self.search(query)]

    def search(self, query):
        import splunklib.results
        resp = self.client.jobs.export('search {}'.format(query),
                                       search_mode='normal',
                                       count=0)
        for result in splunklib.results.ResultsReader(resp):
            if isinstance(result, dict):
                yield result

Sheet.addCommand('^N', 'splunk-query', 'runQuery(input("query: "))')


def main_vsplunk():
    args = get_args()
    config = read_config(args.config)
    status('issue query', priority=-1)
    run(SplunkSheet(name='vsplunk', **config))

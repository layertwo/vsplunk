#!/usr/bin/env python3
import argparse
import configparser
import os
from pathlib import Path

from visidata import asyncthread, ColumnItem, Sheet, deduceType, vd, run, Progress

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
        super().__init__(name, **kwargs)
        self.colnames = {}
        self.columns = []
        self.rows = []
        try:
            import splunklib.client
            self.client = splunklib.client.connect(**kwargs)
            vd.status('connected to splunk', priority=2)
            vd.status('issue query to begin', priority=-1)
        except Exception as e:
            vd.status(e, priority=3)

    def addRow(self, row, index=None):
        super().addRow(row, index=index)
        if isinstance(row, dict):
            for k, v in row.items():
                if k not in self.colnames:
                    if k.startswith('_'):
                        c = ColumnItem(k, type=deduceType(v), width=0)
                    else:
                        c = ColumnItem(k, type=deduceType(v))
                    self.colnames[k] = c
                    self.addColumn(c)

    @asyncthread
    def runQuery(self, query):
        """
        add rows from query results
        """
        # clear the board on new query
        self.colnames = {}
        self.columns = []
        self.rows = []

        with Progress(total=0, gerund='splunking'):
            for row in self.search(query):
                self.addRow(row)

    def search(self, query):
        import splunklib.results
        search_settings = {'search_mode': 'normal',
                           'count': 0}

        if query.startswith('search'):
            resp = self.client.jobs.export(query, **search_settings)
        else:
            resp = self.client.jobs.export('search {}'.format(query),
                                           **search_settings)

        for result in splunklib.results.ResultsReader(resp):
            if isinstance(result, dict):
                yield result

Sheet.addCommand('^N', 'splunk-query', 'runQuery(input("query: ", "splunk"))')


def main_vsplunk():
    args = get_args()
    config = read_config(args.config)
    run(SplunkSheet(name='vsplunk', **config))


if __name__ == '__main__':
    main_vsplunk()

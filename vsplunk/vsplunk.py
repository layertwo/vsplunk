#!/usr/bin/env python3
"""
TODO
- SplunkSheet dive row, check for existing sheet and reload
- Save SplunkSheet as .spl file
- Open .spl file
"""
import re
import argparse
import configparser
import datetime

from visidata import *


__version__ = 0.1
__author__ = 'Lucas Messenger'


class SplunkSheet(Sheet):
    """
    vsplunk main sheet
    """
    def __init__(self, name, **kwargs):
        """
        Init SplunkSheet
        """
        self.filetype = 'spl'
        self.rowtype = 'queries'
        self.rows = []
        self.columns = [
            ColumnItem('query', 0, type=str, width=20),
            ColumnItem('last_run', 1,
                       fmtstr='%Y-%m-%d %H:%M:%S',
                       type=date, width=20)
        ]

        super().__init__(name, **kwargs)
        self.name = name


class SplunkSearchSheet(Sheet):
    """
    Sheet class for issued queries
    """
    def __init__(self, query, **kwargs):
        """
        Init SplunkSearchSheet
        """
        name = re.sub('[^a-zA-Z0-9]', '', query)
        self.rowtype = 'results'
        self.colnames = {}
        self.columns = []

        super().__init__(name, **kwargs)
        self.query = query
        self.reload()

    def addRow(self, row, index=None):
        """
        Add data as new row
        Create new columns if not in sheet
        """
        super().addRow(row, index=index)
        if isinstance(row, dict):
            for k, v in row.items():
                if k not in self.colnames:
                    if k.startswith('_') and not k == '_time':
                        c = ColumnItem(k, type=deduceType(v), width=0)
                    else:
                        c = ColumnItem(k, type=deduceType(v))
                    self.colnames[k] = c
                    self.addColumn(c)

    @asyncthread
    def reload(self):
        """
        Add rows from query results
        """
        self.colnames = {}
        self.columns = []
        self.rows = []

        with Progress(total=0, gerund='splunking'):
            for row in self.search():
                self.addRow(row)

    def search(self):
        """
        Search Splunk with query
        """
        import splunklib.results
        search_settings = {'search_mode': 'normal',
                           'count': 0}

        if self.query.startswith('search'):
            resp = splunkc.jobs.export(self.query, **search_settings)
        else:
            resp = splunkc.jobs.export('search {}'.format(self.query),
                                       **search_settings)

        for result in splunklib.results.ResultsReader(resp):
            if isinstance(result, dict):
                yield result


def get_args():
    """
    get args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='vsplunk configuration file',
                        default=Path('~/.vsplunk'))
    return parser.parse_args()


def read_config(path):
    """
    read ~/.vsplunk for splunk settings
    """
    config = configparser.ConfigParser()
    config.read(path.resolve())

    if 'SPLUNK' in config.sections():
        return config['SPLUNK']

    config['SPLUNK'] = {'host': 'localhost',
                        'port': 8089,
                        'scheme': 'https',
                        'username': 'admin',
                        'password': 'changeme'}

    if not path.exists():
        with path.open_text(mode='w') as fp:
            config.write(fp)
        return read_config(path)
    vd.status('unable to read ~/.vsplunk', priority=3)
    return config['SPLUNK']


def search_splunk():
    """
    Query prompt, query history, search sheet
    """
    query = vd().input('splunk-query: ', 'splunk')
    vd.splunk.addRow((query, datetime.datetime.utcnow()), index=None)
    return vd.push(SplunkSearchSheet(query))


addGlobals(globals())
Sheet.addCommand('^N', 'splunk-query', 'search_splunk()')
SplunkSheet.addCommand(ENTER, 'dive-row', 'vd.push(SplunkSearchSheet(cursorRow[0]))', 'search Splunk with query')
vd.splunk = SplunkSheet('vsplunk')


def main_vsplunk():
    """
    vsplunk main
    """
    args = get_args()
    config = read_config(args.config)
    try:
        import splunklib.client
        global splunkc
        splunkc = splunklib.client.connect(**config)
        vd.status('connected to splunk', priority=2)
        vd.status('issue query to begin', priority=-1)
    except Exception as e:
        vd.status(e, priority=3)

    run(vd.splunk)


if __name__ == '__main__':
    main_vsplunk()

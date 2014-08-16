#!/usr/bin/env python
from __future__ import print_function

import json
import csv
import argparse
import re
import sys

prefix_regex = re.compile(r'([ODP]{1,2})([0-9]+)')


def get_prefix(key, groups):
    res = prefix_regex.search(key)
    return key, groups[res.group(1)], res.group(2)


def main():
    parser = argparse.ArgumentParser(description='NIX Plotter')
    parser.add_argument('csv', type=str)
    parser.add_argument('abstracts', type=str)
    parser.add_argument('groups', type=str)
    args = parser.parse_args()

    idx_len = 30

    with open(args.groups, 'r') as groups_file:
        js = json.load(groups_file)
        groups = {i['short']: i['prefix'] for i in js}

    with open(args.csv, 'rb') as csvfile:
        data_reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        sort_items = {}
        for idx, row in enumerate(data_reader):
            if row[0].startswith('Abstract number'):
                continue
            sys.stderr.write('%03d | [%s] "%s"\n' % (idx, row[0], row[2]))
            value = get_prefix(row[0], groups)
            key = row[2][:idx_len]
            if key in sort_items:
                existing = sort_items[key]
                if existing[0] != value[0]:
                    sys.stderr.write('WARNING: key collision [%s] [%s]\n' % (existing[0], value[0]))
            sort_items[row[2][:idx_len]] = value

    with open(args.abstracts, 'r') as abstracts_file:
        abstracts = json.load(abstracts_file)

    misses = []
    abstract_idx = {}
    for idx, a in enumerate(abstracts):
        title_idx = a['title'][:idx_len]
        abstract_idx[title_idx] = a
        if title_idx not in sort_items:
            misses.append((a['doi'], a['title']))
            continue

        value = sort_items[title_idx]
        a['id'] = int(value[1]) << 16 | int(value[2])
        sys.stderr.write("%s %.10s -> %d\n" % (a['doi'], a['title'], a['id']))

    for key, value in sort_items.iteritems():
        if key not in abstract_idx:
            misses.append((value[0], key))

    sys.stderr.write("Summary:\n")
    sys.stderr.write(" Got %d sort items.\n" % len(sort_items))
    sys.stderr.write(" Got %d abstracts.\n" % len(abstracts))
    sys.stderr.write(" Got %d misse(s):\n" % len(misses))
    for m in misses:
        sys.stderr.write("  [M] %s %.30s...\n" % (m[0], m[1]))

    sys.stdout.write(json.dumps(abstracts, indent=4))
    sys.stderr.write("Wrote %d abstracts\n" % len(abstracts))

if __name__ == '__main__':
    main()
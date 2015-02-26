#!/usr/bin/env python
from __future__ import print_function
from collections import defaultdict
import sys
import json
import re
import string
FIRST_DATAFILE = "../corpus/vocab-0-99-POS.txt"
SECOND_DATAFILE = "../corpus/vocab-100-200-POS.txt"
THIRD_DATAFILE = "../corpus/vocab-201-end-POS.txt"
results = defaultdict(list)

def add_line(line):
    tokens = string.split(line)
    key = tokens[0]
    val = []
    for token in tokens:
        m = re.match('[A-Z]{2,3}', token)
        if m != None:
            val.append(m.group(0))
    results[key] = val

for line in open(FIRST_DATAFILE):
  add_line(line)
for line in open(SECOND_DATAFILE):
  add_line(line)
for line in open(THIRD_DATAFILE):
  add_line(line)

print(json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False))
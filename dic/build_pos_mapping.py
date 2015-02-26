#!/usr/bin/env python
from __future__ import print_function
from collections import defaultdict
import sys
import json
import re
import string
DATAFILE = "../dic/pos_mapping.txt"
results = defaultdict(list)

def add_line(line):
    tokens = string.split(line)
    key = tokens[0]
    val = tokens[1]
    results[key] = val

for line in open(DATAFILE):
  add_line(line)

print(json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False))
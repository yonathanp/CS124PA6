#!/usr/bin/env python3
from collections import defaultdict
import sys
import json
import re
results = defaultdict(list)
last_word = None
for line in open(sys.argv[1]):
  line = line.rstrip()
  m = re.match(r"([\S]+)", line)
  if m != None:
    last_word = m.group(1)
    results[last_word] = []
    continue
  
  m = re.match(r"  (.*)", line)
  if m != None:
    results[last_word].append(m.group(1))
    continue
  print("Unparseable line: {0}".format(line))

print(json.dumps(results, indent=2))

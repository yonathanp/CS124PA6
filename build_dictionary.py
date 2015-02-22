#!/usr/bin/env python3
from collections import defaultdict
import sys
import json
import re
FIRST_DATAFILE = "vocab-0-99.txt"
SECOND_DATAFILE = "vocab-100-200.txt"
THIRD_DATAFILE = "vocab-201-end.txt"
results = defaultdict(list)
last_word = None

def add_line(line):
  global last_word
  line = line.rstrip()
  m = re.match(r"([\S]+)", line)
  if m != None:
    last_word = m.group(1)
    results[last_word] = []
    return
  
  m = re.match("\s+(.*)", line)
  if m != None:
    results[last_word].append(m.group(1))
    return
  print(("Unparseable line: {0}".format(line)), file=sys.stderr)


for line in open(FIRST_DATAFILE):
  add_line(line)
  pass
for line in open(SECOND_DATAFILE):
  add_line(line)
  pass
for line in open(THIRD_DATAFILE):
  m = re.match(r'"(.*?)"\s*=\s*\[(.*?)\]', line.rstrip())
  for word in re.findall(r'"(.*?)"', m.group(2)):
    results[m.group(1)].append(word)

print(json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False))

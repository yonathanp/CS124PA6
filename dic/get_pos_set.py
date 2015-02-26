import json

dictionary_file = "pos_dictionary.json"
pos_set = set()
with open(dictionary_file) as f:
    d = json.load(f)
for i in d:
    for e in d[i]:
        pos_set.add(e)

for p in pos_set:
    print(p)
    
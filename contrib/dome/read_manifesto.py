import json
import sys
import glob

filename = sys.argv[1]
part = sys.argv[2]

with open(filename) as f:
    manifesto = json.load(f)

for pattern in manifesto[part]:
    for file in glob.glob(pattern):
        print(file)


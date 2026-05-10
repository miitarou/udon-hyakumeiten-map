import json

def check_dups(filename, query):
    data = json.load(open(filename))
    dups = [d for d in data if query in d['name']]
    for d in dups:
        print(f"{d['name']} - {d['prefecture']} - {d['years']}")

print("--- UDON ---")
check_dups('data/udon.json', '山下うどん')
check_dups('data/udon.json', '三ツ島')
check_dups('data/udon.json', 'うどん平')

print("--- SOBA ---")
check_dups('data/soba.json', '蕎麦おさめ')

import json

udon = json.load(open('data/udon.json'))
east = sum(1 for d in udon if d.get('region') == 'EAST')
west = sum(1 for d in udon if d.get('region') == 'WEST')
kagawa = sum(1 for d in udon if d.get('region') == 'KAGAWA')
print(f"Udon total: {len(udon)}")
print(f"Udon: EAST {east}, WEST {west}, KAGAWA {kagawa}")

soba = json.load(open('data/soba.json'))
seast = sum(1 for d in soba if d.get('region') == 'EAST')
swest = sum(1 for d in soba if d.get('region') == 'WEST')
print(f"Soba total: {len(soba)}")
print(f"Soba: EAST {seast}, WEST {swest}")

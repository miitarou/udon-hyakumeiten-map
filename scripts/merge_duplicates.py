import json
import os

def merge_duplicates(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    merged_data = {}
    
    for item in data:
        key = f"{item['name'].strip()}_{item['prefecture'].strip()}"
        
        if key in merged_data:
            print(f"  Merging duplicate: {item['name']}")
            # Combine years
            existing_years = merged_data[key]['years']
            new_years = item['years']
            # Merge and sort unique years
            merged_years = sorted(list(set(existing_years + new_years)))
            merged_data[key]['years'] = merged_years
            
            # Use the newer item for other fields (assuming later in the list = newer scrape, e.g., URL might be updated)
            # Actually, it's safer to keep the existing one if it has lat/lng, but they probably both do.
            # We'll just update the years.
        else:
            merged_data[key] = item
            
    final_list = list(merged_data.values())
    
    # Save back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
        
    print(f"  Done. Original count: {len(data)}, New count: {len(final_list)}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    udon_path = os.path.join(base_dir, 'data', 'udon.json')
    soba_path = os.path.join(base_dir, 'data', 'soba.json')
    
    merge_duplicates(udon_path)
    merge_duplicates(soba_path)

if __name__ == '__main__':
    main()

import json
import sys
import os

def check_file(filepath, category):
    print(f"Checking {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to load {filepath}: {e}")
        return False, 1, 0, 0

    if not isinstance(data, list):
        print(f"  [ERROR] Root JSON should be a list in {filepath}")
        return False, 1, 0, 0

    total = len(data)
    errors = 0
    warnings = 0
    duplicates = 0
    
    seen_keys = set()
    
    for i, item in enumerate(data):
        has_error = False
        
        # Check required fields
        for field in ['name', 'category', 'prefecture', 'lat', 'lng', 'years']:
            if field not in item:
                print(f"  [ERROR] Missing required field '{field}' in item {i}: {item.get('name', 'Unknown')}")
                has_error = True
        
        if has_error:
            errors += 1
            continue
            
        # Check specific types and values
        if not isinstance(item['lat'], (int, float)) or not isinstance(item['lng'], (int, float)):
            print(f"  [ERROR] lat/lng not numeric in item {i}: {item['name']}")
            errors += 1
            continue
            
        if not (20.0 <= item['lat'] <= 46.5):
            print(f"  [ERROR] lat out of bounds ({item['lat']}) in item {i}: {item['name']}")
            errors += 1
            continue
            
        if not (122.0 <= item['lng'] <= 154.0):
            print(f"  [ERROR] lng out of bounds ({item['lng']}) in item {i}: {item['name']}")
            errors += 1
            continue
            
        if item['category'] != category:
            print(f"  [ERROR] category mismatch (expected {category}, got {item['category']}) in item {i}: {item['name']}")
            errors += 1
            continue
            
        if not isinstance(item['years'], list) or not all(isinstance(y, int) and 2017 <= y <= 2026 for y in item['years']):
            print(f"  [ERROR] years must be a list of integers between 2017-2026 in item {i}: {item['name']}")
            errors += 1
            continue
            
        url = item.get('url')
        if url and not (url.startswith('http://') or url.startswith('https://')):
            print(f"  [ERROR] url must start with http:// or https:// in item {i}: {item['name']}")
            errors += 1
            continue
            
        # Check for duplicates using name + prefecture
        key = f"{item['name'].strip()}_{item['prefecture'].strip()}"
        if key in seen_keys:
            print(f"  [WARN] Possible duplicate found: {item['name']} ({item['prefecture']})")
            duplicates += 1
            warnings += 1
        else:
            seen_keys.add(key)
            
    print(f"  Summary for {filepath}: Total={total}, Errors={errors}, Warnings={warnings}, Duplicates={duplicates}")
    return errors == 0, errors, warnings, duplicates

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    udon_path = os.path.join(base_dir, 'data', 'udon.json')
    soba_path = os.path.join(base_dir, 'data', 'soba.json')
    
    udon_ok, udon_err, udon_warn, udon_dup = check_file(udon_path, 'udon')
    soba_ok, soba_err, soba_warn, soba_dup = check_file(soba_path, 'soba')
    
    total_err = udon_err + soba_err
    total_warn = udon_warn + soba_warn
    
    print("\n--- Final Summary ---")
    print(f"Total Errors: {total_err}")
    print(f"Total Warnings: {total_warn}")
    
    if total_err > 0:
        print("\nData validation FAILED.")
        sys.exit(1)
    else:
        print("\nData validation PASSED.")
        sys.exit(0)

if __name__ == '__main__':
    main()

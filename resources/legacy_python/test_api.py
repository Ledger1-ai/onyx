import requests
import json

def test_api():
    try:
        response = requests.get('http://localhost:5000/api/schedule?date=2025-06-21')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Slots count: {len(data.get('slots', []))}")
            print(f"Data source: {data.get('data_source', 'unknown')}")
            
            if data.get('slots'):
                first_slot = data['slots'][0]
                print(f"\nFirst slot keys: {list(first_slot.keys())}")
                print(f"First slot ID: {first_slot.get('slot_id', 'NO_SLOT_ID')}")
                print(f"First slot activity: {first_slot.get('activity_type', 'NO_ACTIVITY')}")
                
                # Check if slot_id is present in all slots
                slot_ids = [slot.get('slot_id') for slot in data['slots'][:5]]
                print(f"First 5 slot IDs: {slot_ids}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api() 
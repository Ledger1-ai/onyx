#!/usr/bin/env python3
"""
Debug script to examine schedule slots in database
"""
from database_manager import DatabaseManager
from datetime import datetime
import json

def debug_schedule_slots():
    # Connect to database
    db = DatabaseManager()
    
    print("=== DEBUG: Schedule Slots Analysis ===")
    
    # Get all slots
    all_slots = list(db.db.schedule_slots.find({}))
    print(f"Total slots in database: {len(all_slots)}")
    
    # Group by date field
    date_groups = {}
    for slot in all_slots:
        slot_date = slot.get('date', 'NO_DATE')
        start_time = slot.get('start_time', '')
        
        if slot_date not in date_groups:
            date_groups[slot_date] = []
            
        # Calculate actual date from start_time
        actual_date = "INVALID"
        if start_time:
            try:
                start_time_obj = datetime.fromisoformat(start_time)
                actual_date = start_time_obj.date().strftime('%Y-%m-%d')
            except:
                pass
        
        date_groups[slot_date].append({
            'slot_id': slot.get('slot_id', 'NO_ID')[:8],
            'start_time': start_time,
            'actual_date': actual_date,
            'activity_type': slot.get('activity_type', 'UNKNOWN')
        })
    
    # Print analysis
    for date, slots in sorted(date_groups.items()):
        print(f"\n=== Date Field: {date} ({len(slots)} slots) ===")
        for i, slot in enumerate(slots[:5]):  # Show first 5 slots per date
            mismatch = "❌ MISMATCH" if slot['actual_date'] != date else "✅ OK"
            print(f"  {i+1}. {slot['slot_id']}... | Start: {slot['start_time'][:19]} | Actual Date: {slot['actual_date']} | Type: {slot['activity_type']} | {mismatch}")
        
        if len(slots) > 5:
            print(f"  ... and {len(slots) - 5} more slots")

    # Check for mismatches
    print(f"\n=== MISMATCH ANALYSIS ===")
    total_mismatches = 0
    for date, slots in date_groups.items():
        mismatches = [slot for slot in slots if slot['actual_date'] != date and slot['actual_date'] != 'INVALID']
        if mismatches:
            total_mismatches += len(mismatches)
            print(f"Date {date}: {len(mismatches)} slots with wrong date field")
    
    print(f"Total mismatched slots: {total_mismatches}")
    
    # Cleanup suggestion
    if total_mismatches > 0:
        print(f"\n=== CLEANUP REQUIRED ===")
        print("There are slots with incorrect date fields in the database.")
        print("Run cleanup_schedule_dates() to fix them.")
    
    db.disconnect()

def cleanup_schedule_dates():
    """Fix date field mismatches in database"""
    db = DatabaseManager()
    
    print("=== CLEANING UP SCHEDULE DATE FIELDS ===")
    
    all_slots = list(db.db.schedule_slots.find({}))
    fixed_count = 0
    
    for slot in all_slots:
        slot_id = slot.get('slot_id')
        stored_date = slot.get('date')
        start_time = slot.get('start_time')
        
        if start_time:
            try:
                start_time_obj = datetime.fromisoformat(start_time)
                actual_date = start_time_obj.date().strftime('%Y-%m-%d')
                
                if stored_date != actual_date:
                    # Update the date field
                    result = db.db.schedule_slots.update_one(
                        {"slot_id": slot_id},
                        {"$set": {"date": actual_date}}
                    )
                    if result.modified_count > 0:
                        fixed_count += 1
                        print(f"Fixed slot {slot_id[:8]}... date: {stored_date} -> {actual_date}")
                
            except Exception as e:
                print(f"Error processing slot {slot_id}: {e}")
    
    print(f"\nFixed {fixed_count} slots with incorrect date fields")
    db.disconnect()

if __name__ == "__main__":
    debug_schedule_slots()
    print("\nTo fix the issues, run: python debug_schedule.py cleanup")
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        print("\n" + "="*50)
        cleanup_schedule_dates() 
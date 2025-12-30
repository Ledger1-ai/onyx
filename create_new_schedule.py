#!/usr/bin/env python3
"""
Create a fresh schedule for today and clean up old data
"""
from database_manager import DatabaseManager
from schedule_manager import ScheduleManager
from datetime import datetime
import logging

def clear_old_schedules():
    """Clear old schedule data"""
    db = DatabaseManager()
    
    print("=== CLEARING OLD SCHEDULE DATA ===")
    
    # Get all slots
    all_slots = list(db.db.schedule_slots.find({}))
    print(f"Found {len(all_slots)} total slots")
    
    # Delete all existing slots
    result = db.db.schedule_slots.delete_many({})
    print(f"Deleted {result.deleted_count} schedule slots")
    
    # Delete all existing daily schedules
    result2 = db.db.daily_schedules.delete_many({})
    print(f"Deleted {result2.deleted_count} daily schedules")
    
    db.disconnect()

def create_todays_schedule():
    """Create a fresh schedule for today"""
    db = DatabaseManager()
    schedule_manager = ScheduleManager(db)
    
    print("=== CREATING TODAY'S SCHEDULE ===")
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"Creating schedule for: {today}")
    
    # Create new schedule
    daily_schedule = schedule_manager.create_daily_schedule(today)
    
    print(f"Created schedule with {len(daily_schedule.slots)} slots")
    
    # Verify the slots have correct dates
    for i, slot in enumerate(daily_schedule.slots[:5]):
        slot_date = slot.start_time.date().strftime('%Y-%m-%d')
        print(f"  Slot {i+1}: {slot.start_time} (date: {slot_date}) - {slot.activity_type.value}")
    
    if len(daily_schedule.slots) > 5:
        print(f"  ... and {len(daily_schedule.slots) - 5} more slots")
    
    # Check what's in database now
    db_slots = db.get_schedule_slots(today)
    print(f"\nVerification: Database now has {len(db_slots)} slots for {today}")
    
    db.disconnect()

def verify_schedule():
    """Verify the schedule looks correct"""
    db = DatabaseManager()
    
    print("=== VERIFICATION ===")
    
    today = datetime.now().strftime('%Y-%m-%d')
    slots = db.get_schedule_slots(today)
    
    print(f"Schedule for {today}: {len(slots)} slots")
    
    # Group by actual date
    date_groups = {}
    for slot in slots:
        actual_date = slot.start_time.date().strftime('%Y-%m-%d')
        if actual_date not in date_groups:
            date_groups[actual_date] = 0
        date_groups[actual_date] += 1
    
    print("Slots by actual date:")
    for date, count in sorted(date_groups.items()):
        status = "✅ CORRECT" if date == today else "❌ WRONG DATE"
        print(f"  {date}: {count} slots {status}")
    
    db.disconnect()

if __name__ == "__main__":
    print("=== SCHEDULE RESET AND RECREATION ===")
    print("This will clear all existing schedules and create a fresh one for today")
    
    # Step 1: Clear old data
    clear_old_schedules()
    
    # Step 2: Create today's schedule
    create_todays_schedule()
    
    # Step 3: Verify everything looks good
    verify_schedule()
    
    print("\n=== COMPLETE ===")
    print("Fresh schedule created for today. Try refreshing the dashboard!") 
#!/usr/bin/env python3
"""
Create a schedule for January 11, 2025
"""
from database_manager import DatabaseManager
from schedule_manager import ScheduleManager
from datetime import datetime, date
import logging

def create_jan_schedule():
    """Create a schedule for January 11, 2025"""
    db = DatabaseManager()
    schedule_manager = ScheduleManager(db)
    
    print("=== CREATING SCHEDULE FOR JANUARY 11, 2025 ===")
    
    # Target date: January 11, 2025
    target_date = "2025-01-11"
    print(f"Creating schedule for: {target_date}")
    
    # Create new schedule for this specific date
    daily_schedule = schedule_manager.create_daily_schedule(target_date)
    
    print(f"Created schedule with {len(daily_schedule.slots)} slots")
    
    # Verify the slots have correct dates
    for i, slot in enumerate(daily_schedule.slots[:5]):
        slot_date = slot.start_time.date().strftime('%Y-%m-%d')
        print(f"  Slot {i+1}: {slot.start_time} (date: {slot_date}) - {slot.activity_type.value}")
    
    if len(daily_schedule.slots) > 5:
        print(f"  ... and {len(daily_schedule.slots) - 5} more slots")
    
    # Check what's in database now
    db_slots = db.get_schedule_slots(target_date)
    print(f"\nVerification: Database now has {len(db_slots)} slots for {target_date}")
    
    # Verify the dates in the slots are correct
    date_groups = {}
    for slot in db_slots:
        actual_date = slot.start_time.date().strftime('%Y-%m-%d')
        if actual_date not in date_groups:
            date_groups[actual_date] = 0
        date_groups[actual_date] += 1
    
    print("Slots by actual date:")
    for date, count in sorted(date_groups.items()):
        status = "✅ CORRECT" if date == target_date else "❌ WRONG DATE"
        print(f"  {date}: {count} slots {status}")
    
    db.disconnect()

def check_both_dates():
    """Check what's in the database for both dates"""
    db = DatabaseManager()
    
    print("\n=== DATABASE CONTENTS ===")
    
    # Check January 11, 2025
    jan_slots = db.get_schedule_slots("2025-01-11")
    print(f"January 11, 2025: {len(jan_slots)} slots")
    
    # Check June 12, 2025 (system date)
    june_slots = db.get_schedule_slots("2025-06-12")
    print(f"June 12, 2025: {len(june_slots)} slots")
    
    # Total slots
    all_slots = list(db.db.schedule_slots.find({}))
    print(f"Total slots in database: {len(all_slots)}")
    
    db.disconnect()

if __name__ == "__main__":
    print("=== CREATING SCHEDULE FOR JANUARY 11, 2025 ===")
    
    # Create January schedule
    create_jan_schedule()
    
    # Check both dates
    check_both_dates()
    
    print("\n=== COMPLETE ===")
    print("Schedule for January 11, 2025 is ready!")
    print("You can now view the dashboard for that date.") 
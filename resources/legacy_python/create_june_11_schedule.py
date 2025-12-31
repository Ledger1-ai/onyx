#!/usr/bin/env python3
"""
Create a schedule for June 11, 2025
"""
from database_manager import DatabaseManager
from schedule_manager import ScheduleManager
from datetime import datetime

def create_june_11_schedule():
    """Create a schedule for June 11, 2025"""
    db = DatabaseManager()
    schedule_manager = ScheduleManager(db)
    
    print("=== CREATING SCHEDULE FOR JUNE 11, 2025 ===")
    
    # Target date: June 11, 2025
    target_date = "2025-06-11"
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

def check_both_june_dates():
    """Check what's in the database for both June dates"""
    db = DatabaseManager()
    
    print("\n=== FINAL DATABASE CONTENTS ===")
    
    # Check June 11, 2025
    june_11_slots = db.get_schedule_slots("2025-06-11")
    print(f"June 11, 2025: {len(june_11_slots)} slots")
    if june_11_slots:
        print("  Sample times:", [slot.start_time.strftime('%H:%M') for slot in june_11_slots[:3]])
    
    # Check June 12, 2025
    june_12_slots = db.get_schedule_slots("2025-06-12")
    print(f"June 12, 2025: {len(june_12_slots)} slots")
    if june_12_slots:
        print("  Sample times:", [slot.start_time.strftime('%H:%M') for slot in june_12_slots[:3]])
    
    # Total slots
    all_slots = list(db.db.schedule_slots.find({}))
    print(f"Total slots in database: {len(all_slots)}")
    
    db.disconnect()

if __name__ == "__main__":
    print("=== CREATING SCHEDULE FOR JUNE 11, 2025 ===")
    
    # Create June 11 schedule
    create_june_11_schedule()
    
    # Check both dates
    check_both_june_dates()
    
    print("\n=== COMPLETE ===")
    print("Schedule for June 11, 2025 is ready!")
    print("Now both June 11th and 12th should have proper schedules.") 
#!/usr/bin/env python3
"""
Validation script to assess activity diversification in ScheduleManager.
Uses an in-memory FakeDatabaseManager to avoid MongoDB dependency.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from schedule_manager import ScheduleManager
from data_models import ScheduleSlot, DailySchedule, ActivityType, SlotStatus

class FakeDatabaseManager:
    """Minimal in-memory substitute for DatabaseManager to validate scheduling logic"""
    def __init__(self):
        self.daily_schedules: Dict[str, DailySchedule] = {}
        self.schedule_slots_by_date: Dict[str, List[ScheduleSlot]] = {}

    # Methods used by ScheduleManager
    def save_daily_schedule(self, schedule: DailySchedule) -> bool:
        self.daily_schedules[schedule.date] = schedule
        return True

    def get_daily_schedule(self, date: str) -> Optional[DailySchedule]:
        return self.daily_schedules.get(date)

    def save_schedule_slot(self, slot: ScheduleSlot) -> bool:
        date = slot.start_time.strftime("%Y-%m-%d")
        self.schedule_slots_by_date.setdefault(date, [])
        slots = self.schedule_slots_by_date[date]
        # Replace existing by slot_id or append
        for i, existing in enumerate(slots):
            if existing.slot_id == slot.slot_id:
                slots[i] = slot
                break
        else:
            slots.append(slot)
        return True

    def get_schedule_slots(self, date: str, status: Optional[str] = None) -> List[ScheduleSlot]:
        slots = self.schedule_slots_by_date.get(date, [])
        if status:
            filtered = []
            for s in slots:
                s_status = s.status.value if hasattr(s.status, 'value') else s.status
                if s_status == status:
                    filtered.append(s)
            slots = filtered
        return sorted(slots, key=lambda s: s.start_time)

    def delete_schedule_slot(self, slot_id: str) -> bool:
        for date, slots in list(self.schedule_slots_by_date.items()):
            self.schedule_slots_by_date[date] = [s for s in slots if s.slot_id != slot_id]
        return True

    def delete_daily_schedule(self, date: str) -> bool:
        self.daily_schedules.pop(date, None)
        self.schedule_slots_by_date.pop(date, None)
        return True

    def update_slot_status(self, slot_id: str, status: str, performance_data: Optional[Dict] = None) -> bool:
        for date, slots in self.schedule_slots_by_date.items():
            for s in slots:
                if s.slot_id == slot_id:
                    s.status = SlotStatus(status)
                    if performance_data:
                        s.performance_data = performance_data
                    return True
        return False

    # Strategy-related method; return empty so ScheduleManager creates default
    def get_all_strategy_templates(self):
        return []

def analyze_distribution(slots: List[ScheduleSlot]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for s in slots:
        key = s.activity_type.value if hasattr(s.activity_type, 'value') else str(s.activity_type)
        counts[key] = counts.get(key, 0) + 1
    return counts

def get_max_scroll_streak(slots: List[ScheduleSlot]) -> int:
    max_streak = 0
    current = 0
    for s in slots:
        if s.activity_type == ActivityType.SCROLL_ENGAGE:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak

def main():
    logging.basicConfig(level=logging.INFO)
    date = datetime.now().strftime("%Y-%m-%d")
    db = FakeDatabaseManager()
    sm = ScheduleManager(db_manager=db)
    schedule = sm.get_or_create_daily_schedule(date, force_recreate=True)

    slots = db.get_schedule_slots(date)
    counts = analyze_distribution(slots)
    total = len(slots)
    scroll = counts.get(ActivityType.SCROLL_ENGAGE.value, 0)
    search = counts.get(ActivityType.SEARCH_ENGAGE.value, 0)
    max_streak = get_max_scroll_streak(slots)

    print("Date:", date)
    print("Total slots:", total)
    print("Activity distribution:")
    for k, v in sorted(counts.items(), key=lambda kv: kv[0]):
        print(f"  {k}: {v}")
    ratio = "N/A" if scroll == 0 else f"{search}/{scroll} ({round(search/scroll, 2)} ratio)"
    print("Search vs Scroll:", ratio)
    print("Max consecutive SCROLL_ENGAGE streak:", max_streak)

    # Show a sample of the day
    print("First 32 slots:")
    for s in slots[:32]:
        print(f"{s.start_time.strftime('%H:%M')} - {s.activity_type.value}")

if __name__ == "__main__":
    main()

from data_models import ActivityType

print("Checking ActivityType members...")
found_new = False
for activity in ActivityType:
    print(f"- {activity.name}: {activity.value}")
    if "LINKEDIN_STRATEGY" in activity.name:
        found_new = True

if found_new:
    print("\nSUCCESS: New LinkedIn tasks are visible in data_models.py")
    print("If you don't see them in the Dashboard, please RESTART dashboard_app.py")
else:
    print("\nFAILURE: New LinkedIn tasks are NOT visible.")

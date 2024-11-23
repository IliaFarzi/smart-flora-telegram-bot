from datetime import datetime
import pytz

class IranTime:
    def __init__(self):
        # Set the timezone to Iran Standard Time
        self.timezone = pytz.timezone("Asia/Tehran")

    def get_current_month_name(self):
        # Get the current date and time in Iran's timezone
        now = datetime.now(self.timezone)
        # Return the month name
        return now.strftime("%B")  # Full month name

    def get_current_hour_am_pm(self):
        # Get the current date and time in Iran's timezone
        now = datetime.now(self.timezone)
        # Return the hour in 12-hour AM/PM format
        return now.strftime("%I %p")  # Hour (1-12) and AM/PM


# Example usage
iran_time = IranTime()
print("Current month:", iran_time.get_current_month_name())  # Example: November
print("Current time:", iran_time.get_current_hour_am_pm())   # Example: 02 PM

import datetime

# Get the current date and time
now = datetime.datetime.now()

# Format the date as day-month-year (e.g., 26-02-2026)
formatted_date = now.strftime("%d-%m-%Y")

# Print the result
print(formatted_date)

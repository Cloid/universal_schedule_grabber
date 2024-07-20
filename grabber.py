from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from google.oauth2 import service_account
import time
import csv
from googleapiclient.discovery import build
from selenium.webdriver.support.select import Select
import os
from dotenv import load_dotenv, dotenv_values

# loads .env file at root
# uses vars:
# geckodriver_path - a literal string path to geckodriver.exe (a firefox controller)
# username - username used for myschedule
# password - password used for myschedule account
load_dotenv()

username = os.getenv("username")
password = os.getenv("password")

geckodriver_path = os.getenv("geckodriver_path")

user_index = None

while user_index == None:
    user_index = input("Input an an integer corresponding to week index: ")

    try:
        user_index = int(user_index)
    except ValueError:
        print("Invalid input.")
        user_index = None

# Set up the driver (you'll need to download the appropriate driver for your browser)
service = Service(executable_path=geckodriver_path)
options = webdriver.FirefoxOptions()

driver = webdriver.Firefox(service=service, options=options)

# Open the login page
driver.get("https://myschedule.nbcuni.com/")

# Locate the login elements and enter your credentials
username_field =  driver.find_element(By.ID, "username")
password_field = driver.find_element(By.ID, "password")

username_field.send_keys(username)
password_field.send_keys(password)

# Submit the login form
password_field.send_keys(Keys.RETURN)
time.sleep(2)  # Adjust based on the actual loading time of the schedule page

dropdown = driver.find_element(By.ID, "ddlWeekEnding")
select = Select(dropdown)

select.select_by_index(user_index)

# Navigate to the schedule page
# driver.get("https://company-scheduling-website.com/schedule")

# Wait for the schedule to load and then extract it
time.sleep(4)  # Adjust based on the actual loading time of the schedule page
schedule_html = driver.page_source

driver.quit()

exit()

# parse with beautifulsoup
soup = BeautifulSoup(schedule_html, 'html.parser')

# find tables with grid schedule and legend
schedule_table = soup.find('table', id="gridSchedule")
legend = soup.find('table', id="gridLegend")

# Extract dates from table headers
dates = []
for th in schedule_table.find_all('th'):
    date_span = th.find('span')
    if date_span:
        date_text = date_span.get_text(separator='\n').split('\n')[1].strip()  # Extract the second line (date)
        date = datetime.strptime(date_text, '%m/%d/%Y').strftime('%Y-%m-%d')
        dates.append(date)

legend_map = {}
for row in legend.find_all('tr'):
    cells = row.find_all('td')
    for cell in cells:
        lines = cell.get_text(separator=' ').split(':')
        abbreviation = lines[0].strip() if lines else ''
        venue_name = lines[1].strip().title() if len(lines) > 1 else ''

        if abbreviation and venue_name:
            print(f"Abbreviation: {abbreviation}, Venue Name: {venue_name}")
            legend_map[abbreviation] = venue_name
print(legend_map)

#Find elements containing the schedule data

schedule_data = []

for row in schedule_table.find_all('tr'):

    cells = row.find_all('td')

    for cell_index, cell in enumerate(cells):

        date = dates[cell_index] if cell_index < len(dates) else None
        end_date = date

        lines = []
        # we use seperator to simplify the various line breaks and replace it with \n
        # split the \n so its all seperate unique item per line
        for line in cell.get_text(separator='\n').split('\n'):
            line = line.strip()
            if line:
                lines.append(line)

        if len(lines) >= 4:
            availability = lines[0]
            reg = lines[1]
            time_info = lines[2]
            venue_and_role = lines[3]

            # Parse date and time
            time_parts = time_info.split()
            start_time = time_parts[0]
            end_time = time_parts[2]
            total_time = time_parts[3]

            # Parse venue and role
            venue_role_parts = venue_and_role.split()
            venue = venue_role_parts[0]
            role = venue_role_parts[1]

            if (start_time and end_time):
                start_hour = start_time.split(':')[0]
                end_hour = end_time.split(':')[0]
                print(start_hour)
                print(end_hour)
                if start_hour > end_hour:
                    date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

                    # Add one day to the date
                    next_day = date_obj + timedelta(days=1)

                    # Convert back to string in the same format
                    end_date = next_day.strftime('%Y-%m-%d')


            print(date)

            schedule_data.append({
                'date': date,
                'end_date': end_date,
                'availability': availability,
                'type': reg,
                'start_time': start_time,
                'end_time': end_time,
                'total_time': total_time,
                'venue': venue,
                'role': role
            })

print("scheule_date: " + str(schedule_data))

with open('schedule.csv', mode='w') as file:
    writer = csv.writer(file)
    writer.writerow(['Date', 'End Date', 'Availability','Type', 'Start Time', 'End Time', 'Total Time', 'Venue', 'Role'])
    for event in schedule_data:
        writer.writerow([
            event['date'],
            event['end_date'],
            event['availability'],
            event['type'],
            event['start_time'],
            event['end_time'],
            event['total_time'],
            event['venue'],
            event['role']
        ])

SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)
calendar_id = 'officialcloid@gmail.com'

for event in schedule_data:
    event_body = {
        'summary': str(legend_map[event['venue']]) + " " + str(event['total_time']),
        'start': {
            'dateTime': f"{event['date']}T{event['start_time']}:00",
            'timeZone': 'America/Los_Angeles',  # Adjust to your timezone
        },
        'end': {
            'dateTime': f"{event['end_date']}T{event['end_time']}:00",
            'timeZone': 'America/Los_Angeles',
        },
    }

    service.events().insert(calendarId=calendar_id, body=event_body).execute()
# gridSchedule_lblWeekSunVal_0
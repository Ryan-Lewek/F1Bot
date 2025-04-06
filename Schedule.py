import pandas as pd
import datetime
import pytz

country_flags={
    'Australia':'https://cdn.pixabay.com/photo/2012/04/11/15/43/australia-28586_640.png',
    'Monaco' : 'https://cdn.pixabay.com/photo/2012/04/10/23/11/monaco-26893_1280.png',
    'UK': 'https://cdn.pixabay.com/photo/2022/06/01/16/18/kingdom-7236145_640.png',
    'Italy' : 'https://cdn.pixabay.com/photo/2013/07/13/14/15/italy-162326_640.png',
    'Brazil':'https://cdn.pixabay.com/photo/2021/07/30/12/07/flag-6509488_1280.png',
    'USA':'https://cdn.pixabay.com/photo/2012/04/10/23/21/united-26967_640.png',
    'China':'https://cdn.pixabay.com/photo/2012/04/10/23/01/china-26810_640.png',
    'Japan':'https://cdn.pixabay.com/photo/2013/07/13/14/15/japan-162328_640.png',
    'Bahrain':'https://cdn.pixabay.com/photo/2015/11/04/14/12/flag-1022612_640.png',
    'Saudi Arabia':'https://cdn.pixabay.com/photo/2013/07/13/14/17/saudi-arabia-162413_640.png',
    'Spain' : 'https://cdn.pixabay.com/photo/2012/04/11/15/33/spain-28530_640.png',
    'Canada':'https://cdn.pixabay.com/photo/2012/04/23/16/18/flag-38776_640.png',
    'Austria':'https://cdn.pixabay.com/photo/2023/04/03/02/35/austria-7895853_1280.png',
    'Belgium':'https://cdn.pixabay.com/photo/2015/11/12/15/52/flag-1040530_1280.png',
    'Hungary':'https://cdn.pixabay.com/photo/2012/04/11/15/17/hungary-28446_1280.png',
    'Netherlands':'https://cdn.pixabay.com/photo/2012/04/10/23/11/netherlands-26885_640.png',
    'Azerbaijan':'https://cdn.pixabay.com/photo/2020/02/21/05/49/azerbaijan-4866530_1280.png',
    'Singapore':'https://cdn.pixabay.com/photo/2012/04/10/22/58/singapore-26793_640.png',
    'Mexico':'https://cdn.pixabay.com/photo/2012/04/10/23/24/mexico-26989_640.png',
    'Qatar':'https://cdn.pixabay.com/photo/2013/07/13/14/16/qatar-162396_640.png',
    'UAE':'https://cdn.pixabay.com/photo/2013/07/13/14/17/united-arab-emirates-162451_1280.png'
}
# Define the classes
class GP:
    def __init__(self, name, circuit, round_num, country, flag):
        self.name = name
        self.circuit = circuit
        self.event = []  # List to store associated Event instances
        self.round = round_num
        self.country=country
        self.flag = flag

    def add_event(self, event):
        self.event.append(event)

    def __repr__(self):
        return f"GP(name={self.name}, circuit={self.circuit}, round={self.round}, flag={self.flag}, events={len(self.event)})"


class Event:
    def __init__(self, event_type, datetime, pre_show):
        self.event_type = event_type
        # Ensure datetime is in the format 'YYYY-MM-DDTHH:MM:SSZ'
        self.datetime = self.format_datetime(datetime)
        self.pre_show = pre_show

    def format_datetime(self, datetime_str):
        # Parse the datetime string into a datetime object
        try:
            datetime_obj = pd.to_datetime(datetime_str, errors='coerce')
            # Check if conversion was successful and format it accordingly
            if pd.isnull(datetime_obj):
                return None
            return datetime_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception as e:
            print(f"Error formatting datetime: {e}")
            return None

    def __repr__(self):
        return f"Event(event_type={self.event_type}, datetime={self.datetime}, pre_show={self.pre_show})"


# Function to process the Excel file and create the schedule
def create_race_schedule(file_path):
    # Read Excel file into pandas DataFrame
    df = pd.read_excel(file_path)

    # List to store GP objects
    race_schedule = []

    for index, row in df.iterrows():
        # Extract data from each row
        name = row['Name']
        circuit = row['Circuit']
        country = row['Country']
        round_num = row['round']
        event_type = row['event']
        datetime = row['date']
        pre_show = row['Pre Show']
        flag=country_flags.get(country,None)

        # Check if this GP exists in the race_schedule already
        gp = next((gp for gp in race_schedule if gp.name == name and gp.circuit == circuit), None)

        if not gp:
            # If GP doesn't exist, create a new one and add to race_schedule
            gp = GP(name, circuit, round_num, country, flag)
            race_schedule.append(gp)

        # Create an Event instance for this row
        event = Event(event_type, datetime, pre_show)

        # Add the event to the GP's event list
        gp.add_event(event)

    return race_schedule

def convert_to_est(datetime_str):
    F1_TIMEZONE = pytz.timezone('US/Eastern')

    

    race_datetime = datetime.datetime.fromisoformat(datetime_str).replace(tzinfo=pytz.UTC)
            
    # Convert the UTC time to EST
    race_datetime_est = race_datetime.astimezone(F1_TIMEZONE)

    return race_datetime_est
import pdfplumber
import pandas as pd
import os
from PortCodeParser import *
from datetime import datetime, time

##### HELPER FUNCTIONS #####

def parseTimestamp(ts):
    times = ts.split('-')
    
    # Handle the case where there are not exactly two time components
    if len(times) != 2:
        print(times)
        print('Incompatible timestamp, skipping')
        return ('unknown', 'unknown')

    # Process each time component and replace '24:00' with '23:59'
    cleaned_times = []
    for t in times:
        cleaned_time = t.strip().replace('24:00', '23:59')
        if cleaned_time == '':
            cleaned_times.append('unknown')
        else:
            try:
                time_obj = pd.to_datetime(cleaned_time, format='%H:%M').time()
                cleaned_times.append(time_obj.strftime('%H:%M'))
            except ValueError:
                print(f"Error parsing time: {cleaned_time}")
                cleaned_times.append('unknown')

    return tuple(cleaned_times)

def convertToTimestamp(date_obj, time_str):
    if time_str == 'unknown':
        return 'unknown'
    return pd.Timestamp.combine(date_obj, pd.to_datetime(time_str, format='%H:%M').time())

def cleanBoatName(boatName):
    berth_code = next((code for code in CalendarParser.BERTH_CODES if ((boatName.endswith(' ' + code)) and not (boatName.endswith('SEAS') or boatName.endswith('SEA') or boatName.endswith('BA')))), None)
    #print(berth_code)
    if berth_code:
        boatName = boatName.removesuffix(berth_code)
    #CLEAN AGAIN FOR TRAILING BERTH CODES WRITTEN INCONSISTENTLY (NO SPACE BEFORE)    
    berth_code = next((code for code in CalendarParser.ADDITIONAL_BERTH_CODES if ((boatName.endswith(code)) and not (boatName.endswith('SEAS') or boatName.endswith('SEA') or boatName.endswith('BA')))), None)
    if berth_code and not boatName.endswith('ENCORE'):
        boatName = boatName.removesuffix(berth_code)
    if boatName.endswith('EIGHD') or boatName.endswith('EIGHF') or boatName.endswith('TOA') or boatName.endswith('TOO'):
        boatName = boatName[:-1]
    if boatName.endswith(' CHA'):
        boatName = boatName[:-4]
    return boatName.rstrip()

############################

class CalendarParser:
    PORT_CODES = {'AS' : 'AT SEA', 'ADK': 'ADAK', 'ALT': 'ALERT BAY', 'ANC': 'ANCHORAGE', 'AST': 'ASTORIA', 'ATT': 'ATTU', 'AUK': 'AUKE BAY',
                    'BAR': 'BARONOF WARM SPRINGS', 'BCV': 'BARTLETT COVE', 'BRW': 'POINT BARROW', 'CDV': 'CORDOVA',
                    'CFJ': 'COLLEGE FJORD', 'CG': 'COLUMBIA GLACIER', 'CLD': 'COLD BAY', 'CMR': 'CAMPBELL RIVER', 'CRG': 'CRAIG', 'CRS': 'AT SEA/CRUISING',
                    'DH': 'DUTCH HARBOR', 'ELF': 'ELFIN COVE', 'END': 'ENDICOTT ARM', 'GAM': 'GAMBELL', 'GB': 'GLACIER BAY', 'GI': 'GUARD ISLAND', 'GUS': 'GUSTAVUS',
                    'HNS': 'HAINES', 'HOM': 'HOMER', 'HUB': 'HUBBARD GLACIER', 'HYD': 'HYDER',
                    'ICB': 'ICY BAY', 'ISP': 'ICY STRAIT POINT',
                    'JNU': 'JUNEAU', 'KAK': 'KAKE', 'KDK': 'KODIAK', 'KFJ': 'KENAI FJORD', 'KLM': 'KLEMTU', 'KLW': 'KLAWOCK', 'KTN': 'KETCHIKAN', 'LAX': 'LOS ANGELES',
                    'MET': 'METLAKATLA', 'MFJ': 'MISTY FJORD', 'NAN': 'NANAIMO', 'NOM': 'NOME', 'PEL': 'PELICAN', 'PR': 'PRINCE RUPERT',
                    'PTB': 'PETERSBURG', 'PTS': 'POINT SOPHIA', 'SDG': 'SAN DIEGO', 'SEA': 'SEATTLE', 'SEW': 'SEWARD', 'SFO': 'SAN FRANCISCO', 'SIT': 'SITKA', 'SKG': 'SKAGWAY',
                    'STM': 'ST. MATHEW', 'STP': 'ST. PAUL', 'TA': 'TRACY ARM', 'TB': 'TAYLOR BAY', 'VAN': 'VANCOUVER', 'VDZ': 'VALDEZ',
                    'VIC': 'VICTORIA', 'WHT': 'WHITTIER', 'WRG': 'WRANGELL', 'YAK': 'YAKUTAT'
    }

    BERTH_CODES = ['TEX', 'PTF', 'TWL', 'NHF', 'AS', 'MW', 'CTY', 'ANC', '3', 'CHL', 'AMP', 'POR',
    'DDF', 'RRA', 'AJI', 'OA', 'C', 'AKR', 'WCT', 'AN3', 'AIF', 'ICT', 'WE', 'AN4', 'DW',
    'ANR', 'CON', 'DTN', 'KLW', 'OF', 'ICL', 'STI', '1', 'AKE', 'WW', 'CT', '4',
    '2CR', 'F', 'PIP', 'LTK', '1B', '1CR', '2', 'OSD', 'DYN', '3BR', 'LZ', 
    'PET', 'BRD', 'ALD', 'IWL', 'WP', 'DLY', 'WC2', 'IVF', 'AND',
    'B3T', '3CR', 'SD', 'RR', 'WLD', 'TCL', 'ISD', 'ACT','AJD', 'RRF', 'ORE', '4CR', 'UMC',
    'SHZ', 'ANH', 'OLD', 'CFT', '4BR', '2BR', 'D', 'STO', 'FKL', 'ASD', '1A', 'WC1', 'SLZ', '1BR', 'A', 'FRT', 'CHA']

    ADDITIONAL_BERTH_CODES = ['ANC', 'CHL', 'PET', 'AKR', 'RRF', '2CR', 'AJD', 'AKE', 'ORE', 'AN3', 'AMP',
                              'AS', 'BRD', 'CT', 'CTY', 'FKL', 'RRA', 'STO',
                              'WE', 'WLD', 'WW', 'KLW', 'SD', '1', '2', '3', '4', '2BR', '3CR', '']
                  
    def __init__(self, pdf_path, csv_path, year):
        self.pdf_path = pdf_path
        self.csv_path = csv_path
        self.year = year
        self.df = pd.DataFrame(columns=['date', 'boatName', 'portCode', 'ts_in', 'ts_out'])

    def groupElementsByTwo(self, elements):
        if len(elements) < 2 or len(elements) % 2 != 0:
            print('Error: The list is too short or not divisible by two')
            return []
        elif len(elements) == 2:
            return [(elements[0], elements[1])]
        else:
            return [(elements[0], elements[1])] + self.groupElementsByTwo(elements[2:])
    
    def groupElementsByTwo_LC(self, elements):
        if len(elements) == 1 or len(elements) % 2 != 0 or len(elements) == 0:
            print('Error: The list is too short or not divisible by two')
            #print(elements)
            #print()
            return []
        return [(elements[i], elements[i+1]) for i in range(0, len(elements), 2)]
    
    def parseItineraryCode(self, code):
        s, ts = code
        ports = ['VAN', 'SEW', 'KAK', 'KDK', 'WRG', 'WHT', 'HOM', 'NAN', 'NOM', 'BRW', 'ADK']
        in_port = next((port for port in ports if s.startswith(port)), None)
        if in_port:
            boat = s.replace(in_port, '') # NEED TO REPLACE ONLY LAST OCCURENCE 
        else:
            splits = s.split(' ')
            in_port = splits[0]
            boat = ' '.join(splits[1:])
        return (in_port, cleanBoatName(boat.rstrip()), ts)
    
    def populateDataTable(self, date, parsed_cruise):
        parsed_times = parseTimestamp(parsed_cruise[2])
        date_obj = pd.to_datetime(date)
        
        ts_in = convertToTimestamp(date_obj, parsed_times[0])
        ts_out = convertToTimestamp(date_obj, parsed_times[1])
        
        new_row = {
            'date': date_obj,
            'boatName': parsed_cruise[1],
            'portCode': parsed_cruise[0],
            'ts_in': ts_in,
            'ts_out': ts_out
        }
        #print(new_row)

        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)

    def populateDataTable_old(self, date, parsed_cruise):
        parsed_times = list(parseTimestamp(parsed_cruise[2]))
        if 'unknown' in parsed_times:
            new_row = {
                'date': pd.to_datetime(date),
                'boatName': parsed_cruise[1],
                'portCode': parsed_cruise[0],
                'ts_in': parsed_times[0],
                'ts_out' : parsed_times[1]
            }
        else:   
            new_row = {
                'date': pd.to_datetime(date),
                'boatName': parsed_cruise[1],
                'portCode': parsed_cruise[0],
                'ts_in': pd.Timestamp.combine(pd.to_datetime(date), parsed_times[0]),
                'ts_out' : pd.Timestamp.combine(pd.to_datetime(date), parsed_times[1])
            }
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
    
    def processPDF(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            for count, page in enumerate(pdf.pages):
                print(f'Displaying page {count}')
                tables = page.extract_table()
                if tables is None:
                    print('Table is None')
                    continue
                for row in tables[0]:
                    lines = row.split('\n')
                    date = ' '.join(lines[0].split(' ')[1:]) + ' ' + str(self.year)
                    lines = lines[1:] # continue with data after Date is stored
                    cruises = self.groupElementsByTwo(lines)
                    for cruise in cruises:
                        parsed = self.parseItineraryCode(cruise)
                        self.populateDataTable(date, parsed)
                        
                        print(f'Cruises data on {date}: {parsed}')
                        print(f'original : {cruise[0]}')
    
    def convertCodesToNames(self):
        self.df['portName'] = self.df['portCode'].apply(lambda code: CalendarParser.PORT_CODES.get(code, 'Unknown'))

    def fillNextPorts(self):
        #Needs work as boatNames are not yet cleaned
        self.df['nextPort'] = None
        for index, row in self.df.iterrows():
            boatName = row['boatName']
            next_index = self.df.index[(self.df['boatName'] == boatName) & (self.df.index > index)].tolist()
            if next_index:
                self.df.loc[index, 'nextPort'] = self.df.loc[next_index[0], 'portName']

    def createDailyRows(self):
        """Since each boat should have one daily entry, this method populates the self.df 
           with new rows when boats do not log a port of call and are therefor At Sea
        """
        grouped = self.df.groupby(['boatName'], dropna = True)
        new_rows = []

        for boatName, group in grouped:
            group = group.sort_values(by='date').reset_index(drop=True)
            date_range = pd.date_range(start=group['date'].min(), end=group['date'].max())

            for date in date_range:
                if date not in group['date'].values:
                    new_row = {
                        'date': date,
                        'boatName': boatName,
                        'portCode': 'AS',
                        'ts_in': pd.to_datetime(f"{date} 06:00"),
                        'ts_out': pd.to_datetime(f"{date} 22:00")
                    }
                    new_rows.append(new_row)

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            self.df = self.df.sort_values(by=['boatName', 'date']).reset_index(drop=True)


# Usage
folder = r'./data/calendar/historical_cruise_schedules'
#folder = r'.data//calendar/development_data'

dfs = []

for root, _, files in os.walk(folder):
    for file in files:
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(root, file)
            print(pdf_path)
            csv_path = pdf_path.replace('pdf', 'csv')
            year = pdf_path.split('/')[-1][:4]

            parser = CalendarParser(pdf_path, csv_path, year)
            parser.processPDF()
            parser.createDailyRows()
            parser.convertCodesToNames()
            parser.fillNextPorts()
            parser.df.to_csv(parser.csv_path, index=False)
            dfs.append(parser.df)


# for root, _, files in os.walk(folder):
#     for file in files:
#         if file.lower().endswith('.csv'):
#             print(f'reading {os.path.join(root, file)}')
#             file_path = os.path.join(root, file)
#             try:
#                 # Read each CSV file into a DataFrame
#                 df = pd.read_csv(file_path)
#                 # Append DataFrame to the list
#                 dfs.append(df)
#             except Exception as e:
#                 print(f"Error reading {file_path}: {e}")

# Concatenate all DataFrames in the list into one big DataFrame
big_df = pd.concat(dfs, ignore_index=True)

#output statistics for easy cleanup
grouped = big_df.groupby('boatName').size().reset_index(name='count')
grouped.to_csv('./data/calendar/allyears_allports_claa_groupstats.csv', index=False)

big_df.to_csv('./data/calendar/allyears_allports_claa.csv')






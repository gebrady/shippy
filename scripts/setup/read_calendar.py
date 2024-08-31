import pdfplumber
import pandas as pd

def groupElementsByTwo(list, out):
    if (len(list) == 1) or (len(list)%2 != 0) or (len(list) == 0):
        print('error the list is too short or not divisible by two')
    elif len(list) == 2:
        return out.append((list[0], list[1]))
    else:
        #print(list)
        out.append((list[0], list[1]))
        groupElementsByTwo(list[2:], out)

def parseItineraryCode(triple):
    #print(triple)
    ts = triple[1]
    s = triple[0]
    if s.startswith('VAN'):
        inPort = 'VAN'
        boat = s.replace('VAN','')
    elif s.startswith('SEW'):
        inPort = 'SEW'
        boat = s.replace('SEW','')
    elif s.startswith('KAK'):
        inPort = 'KAK'
        boat = s.replace('KAK','')
    elif s.startswith('KDK'):
        inPort = 'KDK'
        boat = s.replace('KDK','')
    elif s.startswith('WRG'):
        inPort = 'WRG'
        boat = s.replace('WRG','')
    elif s.startswith('WHT'):
        inPort = 'WHT'
        boat = s.replace('WHT','')
    elif s.startswith('HOM'):
        inPort = 'HOM'
        boat = s.replace('HOM','')
    else:
        splits = s.split(' ')
        inPort = splits[0]
        #misc = splits[-1]
        boat = ' '.join(splits[1:])
        #th
    return (inPort, boat, ts)

def populateDataTable(df, date, parsed_cruise):
    new_row = {'date' : pd.to_datetime(date),
               'boatName' : parsed_cruise[1],
               'inPort' : parsed_cruise[0], 
               'ts' : parsed_cruise[2]}
    new_df = pd.DataFrame([new_row])
    df = pd.concat([df, new_df], ignore_index = True)
    return df

year = 2023
pdf_path = r'./data/data/calendar/2023_allports.pdf'
csv_path = r'./data/calendar/2023_allports.csv'
df = pd.DataFrame(columns = ['date', 'boatName', 'inPort', 'ts'])


with pdfplumber.open(pdf_path) as pdf:
    count = 0
    for page in pdf.pages:
        print(f'displaying page {count}')
        #if count > 3:
        #    break
        tables = page.extract_table()
        # Process tables
        print()
        if tables is None:
            print('table is none')
            continue
        for row in tables[0]:
            lines = row.split('\n')
            date = lines[0].split(' ')[1:]
            date = ' '.join(date) + ' ' +  str(year)
            lines = lines[1:]
            cruises = []
            groupElementsByTwo(lines, cruises)
            parsed_cruises = []
            for cruise in cruises:
                parsed = parseItineraryCode(cruise)
                parsed_cruises.append(parsed)
                df = populateDataTable(df, date, parsed)
                

            print(f'cruises data on {date}: {parsed_cruises}')
            print()


        print()
        count+=1
        df.to_csv(csv_path, index=False)



test_list = ['KTN NIEUW AMSTERDAM 2',
             '10:00-18:00',
             'KTN WESTERDAM 1',
             '10:00-18:00',
             'SKG CARNIVAL SPIRIT ORE',
             '07:00-20:00',
             'SKG SAPPHIRE PRINCESS RRA',
             '07:00-20:30',
             'SKG NORWEGIAN JEWEL BRD',
             '08:00-20:00',
             'TA BRILLIANCE OF THE SE',
             '06:00-10:00'
]




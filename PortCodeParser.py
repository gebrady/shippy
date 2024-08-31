import pdfplumber
import pandas as pd
from collections import Counter

##### HELPER FUNCTIONS #####

def value_counts(elements):
    return Counter(elements)

############################

class PortCodeParser:
    SERVICE_CODES = ['P', 'BP', 'BPTG',
                     'BPT', 'B', 'PR', 'BTP',
                     'BG', 'BPG', 'BTGP', 'PB']

    def __init__(self, pdf_path, csv_path):
        self.pdf_path = pdf_path
        self.port_codes_dict = {}

    def processPDF(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            for count, page in enumerate(pdf.pages):
                print(f'Displaying page {count}')
                text = page.extract_text()
                if text is None:
                    print('Page text is None')
                rows = text.split('\n')
                for row in rows[3:-1]:
                    #print(row)
                    codes = row.split(' ')
                    if codes[-1] in PortCodeParser.SERVICE_CODES:
                        codes = codes[:-1]  
                    self.port_codes_dict[codes[0]] = ' '.join(codes[1:])

# Usage
pdf_path = './data/calendar/claa_port_codes.pdf'
csv_path = './data/calendar/claa_port_codes.csv'

parser = PortCodeParser(pdf_path, csv_path)
parser.processPDF()
print(parser.port_codes_dict)


import gspread
import csv
import string
import datetime
import os

sa = gspread.service_account()

def main():
    print("\nPushing Dump/dump.csv to Google Sheets!\n")
    input = "Dump/dump.csv"
    date = datetime.datetime.now()
    sheet = f"SlackData{str(date)[:4]}"
    work = str(date)[5:10]
    clean_data = clean(input)
    toGSheetsMW(sheet, work, clean_data)

def clean(dirty):
    print("parsing data...\n")
    with open(dirty, 'r+') as file:
        hold = []
        hold.append(['Channel', 'Name', 'Email', 'Membership', 'Date/Time (UTC)', 'Thread Reply', 'Workflow'])
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            hold.append(row)
    return hold


def toGSheetsMW(sheet, tab, input):
    try:
        sh = sa.open(sheet)
        print("file exists\n")
    except:
        sh = sa.create(sheet)
        print("file created and shared with jack.countryman@homeinsteadinc.com\n")
        sh.share('jack.countryman@homeinsteadinc.com', perm_type='user', role='owner')
    try:
        worksheet = sh.add_worksheet(title=tab, rows=10000, cols=50)
        print("worksheet created\n")
        toGSheets(worksheet, input)
    except:
        worksheet = sh.worksheet(tab)
        print("worksheet exists, updating\n")
        toGSheets(worksheet, input)

    #os.remove(Dump/dump.csv)

def toGSheets(worksheet, input):
    push = []
    line=1
    final=""
    for row in input:
        push.append(row)
        col = 1
        for i in row:
            column = string.ascii_uppercase[col]
            final=f"{column}{line}"
            col += 1
        line += 1
    final = 'A1:'+final
    worksheet.update(final, push)
    print("UPDATE COMPLETE!\n")

if __name__ == "__main__":
    main()
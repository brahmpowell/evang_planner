import csv
import json

def read_json(fpath, default=None, mode='r'):
    try:
        with open(fpath, mode, encoding='utf-8') as jf:
            data = json.load(jf)
    except FileNotFoundError:
        if default is None:
            raise
        else:
            return default
    except:
        raise
    return data

def save_json(fpath, data, mode='w'):
    with open(fpath, mode) as jf:
        json.dump(data, jf)

def read_csv(fpath, delimiter=',', newline='', default=None):
    try:
        with open(fpath, mode='r', newline=newline, encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            data = [row for row in csv_reader]
    except FileNotFoundError:
        if default is None:
            raise
        else:
            return default
    except:
        raise
    return data

def strip_string(s):
    return ("".join(char for char in s if char.isalpha())).lower()

def str2int(s, default=0):
    val = "".join(char for char in s if char.isdigit())
    return int(val) if len(val) > 0 else default

def print_cols(rows, sep=' | '):
    if len(rows) > 0:
        widths = [0 for _ in rows[0]]
    else:
        print('No data.')
    for row in rows:
        for i in range(len(row)):
            if len(row[i]) > widths[i]:
                widths[i] = len(row[i])
    for row in rows:
        new_row = []
        for i in range(len(row)):
            new_row.append(row[i] + ' '*(widths[i]-len(row[i])))
        print(sep.join(new_row))
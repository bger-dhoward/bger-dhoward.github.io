import argparse
import tkinter as tk
from tkinter import filedialog

parser = argparse.ArgumentParser(prog = "COAA Survey Summarizer")
parser.add_argument('question_num', help='Which question to summarize (q1, q2, q3)')
#parser.add_argument('--file', help='Name of source data file to pull responses from in case of automation errors') # TODO: IMPLEMENT THIS FUNCTIONALITY
parser.add_argument('--csv', help="Name of csv file to pull responses from in case of automation errors")
parser.add_argument('--excel', help="Name of .xlsx file to pull responses from.  Must be downloaded from MS Forms")
parser.add_argument('--askfile', help="Leave blank to ask file to open", action='store_true')
parser.add_argument('--test', help="test number", action='store_true')
args = parser.parse_args()

print(args)

root = tk.Tk()
root.withdraw()

filename = filedialog.askopenfilename(title='Select .XLSX data file', filetypes=[("Excel (.xlsx)", ".xlsx")])

print(type(filename))
print(filename)


input('done?')
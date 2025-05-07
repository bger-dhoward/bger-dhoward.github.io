import ollama
import os
import csv
from jinja2 import Environment, FileSystemLoader
import argparse
import openpyxl
import tkinter as tk
from tkinter import filedialog
from pathlib import Path


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template('coaa_template.txt')

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
#RESPONSE_SPREADSHEET_ID = "1cHKk2LKpIdgBpFtBOD-awZhULixMA2iQwk_fRSUjlMA"
RESPONSE_SPREADSHEET_ID = "1sPpnOZzu5X9uzwhgP1gVRLmIcajrmtw9SKM_E8jqCQs"
#RESPONSE_RANGE_NAME = "Responses!A1:F100"
N_TESTS = 20

MIN_RESPONSE_LENGTH = 5

RESPONSE_RANGES = {"q1": "Q1!A1:D200",
                   "q2": "Q2!A1:D200",
                   "q3": "Q3!A1:D200",
                   }

criteria_options = {
    1:"Identify common themes as summaries. Provide only the summaries without any introductory text. Provide each as a single phrase or sentence on its own line. Separate out any responses that seem to be not related to the question and provide them at the end, prefixed with a '$' symbol.",
    2:"Identify common themes as summaries. Provide only the summaries without any introductory text. Provide each as a single phrase or sentence on its own line. Provide at most 3 summaries. Prefix each summary with a '$' sign.",
    }

question_definitions = {"q1": "What is the greatest measure of project success to you?",
                        "q2": "What is the biggest key to facilitating open dialog?",
                        "q3": "What aspect of the project charter process would you like to know more about before implementing on one of your projects?",                        
                        }

def get_user_responses_from_csv(filename):
    with open(filename) as file:
        reader = csv.reader(file)
        responses = list(reader)
    
    return responses

def get_user_response_from_excel(filename):
    wb = openpyxl.load_workbook(filename=filename)
    ws = wb[wb.sheetnames[0]]
    data = list(ws.values)
    return data[1:]

def get_user_responses_from_cloud():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    
    try:
        service = build("sheets", "v4", credentials=creds)
        
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=RESPONSE_SPREADSHEET_ID, range=RESPONSE_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])
        
        if not values:
            print('no data found... is something wrong?')
            return
        return values[1:]
    except HttpError as err:
        print(err)

def get_user_responses(filename):
    with open(filename, encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        data = list(reader)
    return data

def generate_test_prompt(data):
    category = data[0][0]
    user_responses = [r[0] for r in data[1:]]
    #print(user_responses)
    user_resp_string = "\n".join(user_responses)
    prompt = f"A group of users in a kickoff meeting for VT university School of Medicine new building project were asked to provide responses for a prompt of '{category}'. Their responses will be at the end of this message.  Provide about 5 concise single short sentence summaries that synthesize these responses into a set of potential guiding principles for the design of the project. Prefix each summary sentence with '%'. Do not include any introductory text or line number. These are their responses:\n{user_resp_string}"
    return prompt

def generate_bger_survey_prompt(question, responses_text, criteria):
    prompt = f"""An interal survey asked the following question: '{question}'.
        The responses will be provided at the end of this message.
        Provide summaries of the responses using this criteria: {criteria}.
        These are the responses: \n{responses_text}
    """
    return prompt

def generate_coaa_survey_prompt(question, response_text, criteria):
    prompt = f"""A survey of conference attendees asked the following question: '{question}'.
    The responses will be provided at the end of this message.
    Provide summaries of the survey responses using this criteria: '{criteria}'.
    These are the responses:
    {response_text}
"""
    return prompt


def ask_model(prompt):
    response = ollama.chat(model="llama3.2", messages=[
        {'role':'user',
         'content':prompt}
    ])
    return response.message.content


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog = "COAA Survey Summarizer")
    parser.add_argument('question_num', help='Which question to summarize (q1, q2, q3)')
    parser.add_argument('--file', help='Name of source data file to pull responses from in case of automation errors') # TODO: IMPLEMENT THIS FUNCTIONALITY
    parser.add_argument('--csv', help="Name of csv file to pull responses from in case of automation errors")
    parser.add_argument('--excel', help="Name of .xlsx file to pull responses from.  Must be downloaded from MS Forms")
    parser.add_argument('--askfile', help="Leave blank to ask file to open", action='store_true')
    parser.add_argument('--test', help="Generate a number of test responses from AI to terminal - no HTML output.", action='store_true')
    args = parser.parse_args()
    question_num = args.question_num.lower()

    if question_num in RESPONSE_RANGES.keys():
        RESPONSE_RANGE_NAME = RESPONSE_RANGES[question_num]
    else:
        print(f"Question value '{question_num}' is not a valid question.")
        exit()

    question_text = question_definitions[question_num]
    
    if args.csv:
        responses = [row[0] for row in get_user_responses_from_csv(args.csv)]
        print(responses)
    elif args.excel:
        data = get_user_response_from_excel(args.excel)
        responses = [row[5] for row in data if len(row[5]) >= MIN_RESPONSE_LENGTH]
    elif args.askfile:
        root = tk.Tk()
        root.withdraw()
        picked_file = filedialog.askopenfilename(title='Select .XLSX data file', filetypes=[("Excel (.xlsx)", ".xlsx")])
        data = get_user_response_from_excel(picked_file)
        responses = [row[5] for row in data if len(row[5]) >= MIN_RESPONSE_LENGTH]
    else:
        values = get_user_responses_from_cloud()
        responses = [row[2] for row in values if len(row[2]) >= MIN_RESPONSE_LENGTH]
    response_string = "\n".join(responses)

    filename = question_num + "_summary.html"
    criteria = criteria_options[2]

    prompt = generate_coaa_survey_prompt(question_text, response_string, criteria)

    break_tab = "\n\t"
    meta_data = f"""
==========
Question number:        {question_num}
Question text:          {question_text}
Number of responses:    {len(responses)}

Response text: 
{break_tab.join(responses)}

==========

Criteria: {criteria}

Prompt: {prompt}

==========
"""

    print(meta_data)
    if args.test:
        print("=========\n\nTESTING\n\n==========")
        print(f"# of tests: {N_TESTS}")
        for i in range(N_TESTS):
            model_response = ask_model(prompt)
            print(f"=========\nModel Response TEST # {i}\n\n {model_response}")
    else:
        model_response = ask_model(prompt)

        print(f"=========\nModel Response\n\n {model_response}")

        onedrive_path = Path(r'C:\Users\dhoward\VMDO Architects\COAA Charlottesville 2025 - summary web pages')


        summaries = [s.strip()[1:] for s in model_response.split("\n") if len(s) > 5 and s.startswith('$')]
        summaries = summaries[:3]
        #results_filename = "pages/" + filename + ".html"
        results_filepath = onedrive_path / filename
        context = {
            "summaries": summaries,
            "responses": responses,
            "question_number": question_num,
            "question_text": question_text
        }
        
        with open(results_filepath, 'w', encoding='utf-8') as results_file:
            results_file.write(template.render(context))
            print('done onedrive')
        
        local_repo = Path(r"C:\Users\dhoward\Documents\PYTHON\bger-dhoward.github.io\COAA_chartersummary\pages")
        local_repo_filepath = local_repo / filename

        with open(local_repo_filepath, 'w', encoding='utf-8') as results_file:
            results_file.write(template.render(context))
            print('done local repo')
    
    print(f"\n\n{'+'*10}\nDone!\n{'='*10}")


import ollama
import os
import csv
from jinja2 import Environment, FileSystemLoader

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template('page_template.txt')

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
RESPONSE_SPREADSHEET_ID = "1cHKk2LKpIdgBpFtBOD-awZhULixMA2iQwk_fRSUjlMA"
RESPONSE_RANGE_NAME = "Responses!A1:F100"

def get_user_responses_from_cloud():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
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
        return values
    except HttpError as err:
        pritn(err)

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
        These are the responses: {responses_text}
    """
    return prompt


def ask_model(prompt):
    response = ollama.chat(model="llama3.2", messages=[
        {'role':'user',
         'content':prompt}
    ])
    return response.message.content


if __name__ == "__main__":
    values = get_user_responses_from_cloud()
    q1_responses = [row[2] for row in values]
    q2_responses = [row[3] for row in values]
    q3_responses = [row[4] for row in values]
    
    """
    print(os.getcwd())
    for filename in [fn for fn in os.listdir() if fn.endswith('.csv')]:
        data = get_user_responses(filename)
        category = data[0][0]
        # print(data)
        prompt = generate_test_prompt(data)
        print(filename, data[0])
        response = ask_model(prompt)
        summary = response.split("\n")

        context = {"category": category,
                   "summary": summary}
        #print(response)
        #print('\n\n')
        #input('next?\n\n')

        results_filename = category + ".html"
        with open(results_filename, 'w', encoding='utf-8') as results:
            results.write(template.render(context))
    """
    
    input('hit enter to exit')


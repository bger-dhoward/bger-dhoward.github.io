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

criteria_options = {
    1:"Identify common themes as summaries. Provide only the summaries without any introductory text. Provide each as a single phrase or sentence on its own line. Separate out any responses that seem to be not related to the question and provide them at the end, prefixed with a '$' symbol.",
    2:"Identify common themes as summaries. Provide only the summaries without any introductory text. Provide each as a single phrase or sentence on its own line. Provide at most 3 summaries",
    }


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


def ask_model(prompt):
    response = ollama.chat(model="llama3.2", messages=[
        {'role':'user',
         'content':prompt}
    ])
    return response.message.content


if __name__ == "__main__":
    values = get_user_responses_from_cloud()
    q1_responses = "\n".join([row[2] for row in values])
    q2_responses = "\n".join([row[3] for row in values])
    q3_responses = "\n".join([row[4] for row in values])

    q1 = "What would be your ideal 'work-from-home' setup? (Location, atmosphere, tools, etc)"
    q2 = "What is the most exciting or interesting aspect of one of your current projects?"
    q3 = "If you use any AI tools for work, what is the most common way you use it?"

    filenames = ["work_from_home_setup",
                 "interesting_project",
                 "ai_tool_use"]

    criteria = criteria_options[2]

    q_sets = zip([q1, q2, q3],[q1_responses, q2_responses, q3_responses], filenames)

    for q, r, filename in q_sets:
        prompt = generate_bger_survey_prompt(q, r, criteria)
        print("============\nQuestion\n")    
        print(q)
        print("============\nResponses\n")
        print(r)
        print("============\nPrompt\n")  
        print(prompt)
        response = ask_model(prompt)
        print("============\nAI Summary\n")
        print(response)
        print("\n")
        summary = response.split("\n")

        results_filename = "pages/" + filename + ".html"
        category = filename
        context = {"category": category,
                   "summary": summary}
        with open(results_filename, 'w', encoding='utf-8') as results_file:
            results_file.write(template.render(context))
    
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


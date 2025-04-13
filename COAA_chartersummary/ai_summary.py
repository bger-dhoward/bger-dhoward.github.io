import ollama
import os
import csv
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template('page_template.txt')


# os.chdir(r'C:\Users\howar\OneDrive - ballingercloud\Documents\aisummary')

def get_user_responses(filename):
    with open(filename, encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        data = list(reader)
    return data

def generate_prompt(data):
    category = data[0][0]
    user_responses = [r[0] for r in data[1:]]
    #print(user_responses)
    user_resp_string = "\n".join(user_responses)
    prompt = f"A group of users in a kickoff meeting for VT university School of Medicine new building project were asked to provide responses for a prompt of '{category}'. Their responses will be at the end of this message.  Provide about 5 concise single short sentence summaries that synthesize these responses into a set of potential guiding principles for the design of the project. Prefix each summary sentence with '%'. Do not include any introductory text or line number. These are their responses:\n{user_resp_string}"
    return prompt

def ask_model(prompt):
    response = ollama.chat(model="llama3.2", messages=[
        {'role':'user',
         'content':prompt}
    ])
    return response.message.content


if __name__ == "__main__":
    print(os.getcwd())
    input('continue?')
    for filename in [fn for fn in os.listdir() if fn.endswith('.csv')]:
        data = get_user_responses(filename)
        category = data[0][0]
        # print(data)
        prompt = generate_prompt(data)
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

    
    input('hit enter to exit')


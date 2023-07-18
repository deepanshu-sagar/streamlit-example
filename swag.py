import streamlit as st
import requests
import json
import subprocess
import time
import tempfile
import os

def fetch_and_parse_swagger(url):
    response = requests.get(url)
    data = json.loads(response.text)

    curl_commands = {}
    for path, path_data in data["paths"].items():
        for method, method_data in path_data.items():
            curl_command = f"curl -X {method.upper()} 'https://apps.pubmatic.com{path}'"
            if "parameters" in method_data:
                for param in method_data["parameters"]:
                    if param["in"] == "query":
                        curl_command += f" --data-urlencode '{param['name']}={{}}'"
                    elif param["in"] == "path":
                        curl_command += f" -d '{param['name']}={{}}'"
            if "requestBody" in method_data:
                curl_command += f" -d '{json.dumps(method_data['requestBody']['content']['application/json']['schema']['example'])}'"
            curl_commands[f"{method.upper()} {path}"] = curl_command

    return curl_commands

def run_cmd(prompt_text, pyfile_text):
    start_time = time.time()

    prompt_fd, prompt_path = tempfile.mkstemp()
    pyfile_fd, pyfile_path = tempfile.mkstemp()

    with os.fdopen(prompt_fd, 'w') as prompt_file:
        prompt_file.write(prompt_text)
        
    with os.fdopen(pyfile_fd, 'w') as pyfile_file:
        pyfile_file.write(pyfile_text)

    cmd = ["bito", "-p", prompt_path, "-f", pyfile_path]
    output = subprocess.check_output(cmd)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Clean up temporary files
    os.unlink(prompt_path)
    os.unlink(pyfile_path)
    
    return output, total_time

st.title('Swagger to cURL Converter')

# URL of the Swagger JSON file
url = st.text_input('Enter Swagger URL', 'https://apps.pubmatic.com/heimdall/v2/api-docs')

if st.button('Fetch and Convert'):
    st.text('Fetching Swagger and Converting to cURL...')
    curl_commands = fetch_and_parse_swagger(url)

    # Define default prompt text
    prompt_text = """
    Act as a software tester...
    """

    # Execute each cURL command and collect responses
    responses = []
    for command in curl_commands.values():
        output, total_time = run_cmd(prompt_text, command)
        responses.append(output.decode('utf-8'))

    # Display the responses
    st.header('Responses')
    for response in responses:
        st.text(response)
    ## Display the total time taken
    st.text(f"Total time taken: {total_time} seconds")
    
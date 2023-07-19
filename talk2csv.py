import streamlit as st
import requests
import json
import subprocess
import time
import tempfile
import os, io
import pandas as pd
import openpyxl

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

# Define the function to prepare a prompt
def prepare_prompt(operation):
    prompt = f"""Write a pytest function to perform the following operation:
    {operation}
    Keep the function name unique as per api endpoint and operation.
    Please ensure to include appropriate setup, test execution, and teardown phases in the pytest function.
    """
    return prompt

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
    1. **CURL Call Details:**
   - **HTTP Method:** (Extracted from CURL: GET, POST, PUT, DELETE, etc.)
   - **API Endpoint:** (Extracted from CURL: `/<service>/<API>`)
   - **Headers:** (Extracted from CURL: `<Header>: <Value>`)
   - **Request Payload/Data/File:** (Extracted from CURL if POST/PUT, as per IAB standards)

2. **Expected Response Details:**
   - **Format:** (Based on response: CSV, JSON, etc.)
   - **Expected status codes:** (Based on response: 200, 201, 400, 401, 403, 404, 500, etc.)

Using the provided CURL Call and Expected Response details, create a table with the following fields for each test case:

- **Sr.No:** _(Test case number)_
- **Test Case:** _(Description derived from the CURL call and Expected Response)_
- **Prerequisite:** _(Any setup needed, derived from the CURL call)_
- **Test Steps:** _(Execution steps, based on the CURL call)_
- **Expected Results:** _(Outcome and status code, based on the Expected Response)_
- **Priority:** _(Assigned based on impact: P1/P2/P3)_
- **Positive/Negative Case:** _(Specify type, usually Positive for correct CURL call and Negative for tests with incorrect input or setup)_

only P1 cases required.  For each of these, a new row in the table would be added. Use the details provided by the user to generate each field in the table. The output should cover all the points in the test case document in a tabular format. 
    """

    # Execute each cURL command and collect responses
    responses = []
    for command in list(curl_commands.values())[:2]:
        output, total_time = run_cmd(prompt_text, command)
        responses.append(output.decode('utf-8'))

    # Display the responses
    st.header('Responses')
    #for response in responses:
    #    st.text(response)

    # Split the first response to get the header and data
    first_response = responses[0].split('\n\n')[1].strip()

    # Convert the first response to a DataFrame
    df = pd.read_csv(io.StringIO(first_response), sep='|', skipinitialspace=True, engine='python')

    
    # Prepare an empty Python file
    py_content = ""

    # Process the rest of the responses
    for response in responses[1:]:
        table_data = response.split('\n\n')[1].strip()

        # Add a check to ensure the response contains data
        if '\n' in table_data:
            # Convert the response to a DataFrame, ignoring the first row (header)
            df_response = pd.read_csv(io.StringIO(table_data), sep='|', skipinitialspace=True, skiprows=1, header=None, engine='python')

            # Set the column names to match the original DataFrame
            df_response.columns = df.columns

            # Append the DataFrame to the original DataFrame
            # Append the DataFrame to the original DataFrame
            df = pd.concat([df, df_response])

    # Export the DataFrame to a CSV file
    df.to_csv('response_table.csv', index=False, header=True)

    # Download the CSV file
    with open('response_table.csv', 'rb') as file:
        file_data = file.read()

    st.download_button(label='Download Test Cases', data=file_data, file_name='response_table.csv')

if st.button('Fetch and prepare test cases'):
    st.text('Fetching Swagger and Converting to pytest functions...')
    curl_commands = fetch_and_parse_swagger(url)
    responses = []
    for command in list(curl_commands.values())[:2]:
        # Prepare the prompt text
        prompt_text = prepare_prompt(command)  # Assuming 'command' contains all the information needed for the prompt
        
        # Run the command and store the response
        output, total_time = run_cmd(prompt_text, command)
        responses.append(output.decode('utf-8'))

    
    # Prepare an empty Python file
    py_content = ""

    # Process the rest of the responses
    import re
    for response in responses:
        code = re.search('```python(.+?)```', response, re.DOTALL)
        if code:
            py_content += code.group(1).strip() + "\n\n"

    # Write the Python content to a file
    with open('pytest_functions.py', 'w') as file:
        file.write(py_content)

    # Download the pytest file
    with open('pytest_functions.py', 'rb') as file:
        file_data = file.read()

    st.download_button(label='Download Pytest File', data=file_data, file_name='pytest_functions.py')
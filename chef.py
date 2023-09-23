"""
requirements.txt contents:
streamlit
sqlite3
hashlib
"""

import os
import subprocess
import tempfile
import time
import streamlit as st
import sqlite3
import hashlib
import requests
import json
import os, io
import pandas as pd

# Constants
DB_NAME = "users.db"

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_users_table():
    """Create a table for users in the SQLite database."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL UNIQUE,
             password TEXT NOT NULL);''')

def create_diet_plans_table():
    """Create a table for diet plans in the SQLite database."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS diet_plans
            (plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER REFERENCES users(id),
             plan_content TEXT NOT NULL,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);''')

def insert_into_diet_plans(user_id, plan_content):
    """Insert a new diet plan into the SQLite database."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''INSERT INTO diet_plans (user_id, plan_content)
                        VALUES (?, ?);''', (user_id, plan_content))


def register(username, password):
    """Register a new user in the database."""
    with sqlite3.connect(DB_NAME) as conn:
        try:
            conn.execute(f"INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, hash_password(password)))
            return True
        except sqlite3.IntegrityError:
            return False  # User already exists

def login(username, password):
    """Verify if login credentials are valid."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(f"SELECT password FROM users WHERE username = ?", (username,))
        db_password = cursor.fetchone()
        if db_password and db_password[0] == hash_password(password):
            return True
    return False

# Create table if not exists
create_users_table()

# Check for session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''


# If not logged in, show Login/SignUp
if not st.session_state.logged_in:
    menu = ["Login", "SignUp"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.title("Signup/Signin Page")
        st.subheader("Signup First")
        st.subheader("Login from Left sidebar using your Username and Password")
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            if login(username, password):
                st.success(f"Welcome {username}")
                st.session_state.logged_in = True
                st.session_state.username = username
                # Re-render the page after successful login
                st.experimental_rerun()
            else:
                st.warning("Invalid Username/Password")

    elif choice == "SignUp":
        st.title("Signup/Signin Page")
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')
        if st.button("Signup"):
            if new_password == confirm_password:
                if register(new_user, new_password):
                    st.success(f"Successfully created a new account: {new_user}")
                else:
                    st.warning("Username already exists")
            else:
                st.warning("Passwords do not match")

# If logged in, show Home or other pages
else:
    st.subheader(f"Welcome to Home, {st.session_state.username}!")
    # Rest of your app content for authenticated users
    st.title("Your personalised Fitness Assistant")
    st.subheader("Please enter your details below to get started.")
    st.markdown("#### Note: All details are kept confidential and are not stored anywhere.")


    # Create some empty space below the links to ensure the rest of the content is pushed downwards
    empty_space_below = [st.empty() for _ in range(6)]

    def run_cmd(prompt_text):
        start_time = time.time()
        print (start_time)
        # Create a temporary file and write the prompt_text into it
        prompt_fd, prompt_path = tempfile.mkstemp()
        pyfile_path="tmp"
        try:
            with os.fdopen(prompt_fd, 'w') as prompt_file:
                print (f"{prompt_text}")
                prompt_file.write(prompt_text)
            with open(pyfile_path, 'w') as prompt_file:
                print ("")
                prompt_file.write("prompt_text")

            print ("opening subprocess")
            p2 = subprocess.Popen(["bito", "-p", prompt_path, "-f", pyfile_path], stdout=subprocess.PIPE)  # added stdout=subprocess.PIPE
            output, _ = p2.communicate()  # Get output once here
        except subprocess.CalledProcessError as e:
            print(f"Subprocess returned error: {e.output}")
            output = e.output
        finally:
            # Ensure the temporary file is deleted even if an error occurs
            os.unlink(prompt_path)

        end_time = time.time()
        total_time = end_time - start_time

        return output  # Return the stored output, decoded from bytes to string
    
    def run_cmd_1(prompt_text, pyfile_text):
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

    def generate_diet_plan(goals,preference):
        """Generate a diet plan based on goals using OpenAI."""
        
        if not goals:
            return "Please select at least one goal to get a diet plan."
        if preference == "Both":
            preference = "Veg / Non-Veg :Any. "

        prompt = f"Please provide a diet plan for the following goals: {' and '.join(goals)}. Break it down into Breakfast, Lunch, and Dinner. Take note that Diet Plan is to be created as per the person is living in Pune, India and is {preference} person. Try to keep the Diet Plan Cost effective where ever possible. Do not mention this location and cost effective information in the response. Add Approx. Calorie Details for Each by each individual Meal and By Breakfast/ Lunch/ Dinner As well. "
        output = run_cmd(prompt)
        return output
    

    def generate_workout_plan(level,time):
        """Generate a workout plan based on goals using OpenAI."""

        prompt = f"Please provide a free body workout plan suitable for a {level}. Break it down into Warm-up, Main Workout, and Cool Down sessions. Include details such as exercises to be performed, repetitions, sets, and rest intervals. Also, provide Approximate Calories Burnt for each segment and the Total Session Time of {time} mins. Ensure that the plan requires no equipment."
        output = run_cmd(prompt)
        return output
    
    def suggest_ingredients(cuisine,vegnonveg):
        prompt = f"What are some typical ingredients used in {cuisine} cuisine for {vegnonveg} person? only ingriedients names. in comma separated format. in the style of tarla dalal and sanjeev kapoor. Example : Onion, Lettuce, Carrot"
        output = run_cmd(prompt)
        return output

    def generate_recipe(ingredients, cuisine,vegnonveg):
        prompt = f"Create a {cuisine} recipe for {vegnonveg} person using the following ingredients: {ingredients} in the style of tarla dalal and sanjeev kapoor."
        output = run_cmd(prompt)
        return output
    
    # Initialize session state variables if not already present
    if not hasattr(st.session_state, 'submitted_details'):
        st.session_state.submitted_details = False
    if not hasattr(st.session_state, 'bmi'):
        st.session_state.bmi = None
    if not hasattr(st.session_state, 'category'):
        st.session_state.category = None
    if not hasattr(st.session_state, 'name'):
        st.session_state.name = ""



    # Details input container
    details_container = st.container()
    with details_container:
        if not st.session_state.submitted_details:
            st.session_state.name = st.text_input("Name:")
            age = st.number_input("Age:", min_value=1, max_value=120)
            height = st.number_input("Height (in cm):", min_value=50.0, max_value=250.0)
            weight = st.number_input("Weight (in kg):", min_value=1.0, max_value=200.0)

            if st.button('Submit Details'):
                st.session_state.submitted_details = True
                height_m = height / 100.0
                st.session_state.bmi = weight / (height_m ** 2)

                # Determine BMI Category
                if st.session_state.bmi < 18.5:
                    st.session_state.category = "Underweight"
                elif 18.5 <= st.session_state.bmi < 24.9:
                    st.session_state.category = "Normal weight"
                elif 25 <= st.session_state.bmi < 29.9:
                    st.session_state.category = "Overweight"
                else:
                    st.session_state.category = "Obesity"

    def format_diet_plan(plan_bytes):
        # Decode bytes to string
        plan_str = plan_bytes.decode('utf-8')
        
        # Split string by line breaks and format
        lines = plan_str.split("\n")
        formatted_plan = ""
        for line in lines:
            if line:
                # If it's a header line (like "Breakfast:")
                if ":" in line:
                    formatted_plan += f"\n\n**{line}**\n"
                else:
                    # If it's a list item (like "2-3 boiled eggs")
                    if "-" in line[0:2]:
                        formatted_plan += f"- {line[2:].strip()}\n"
                    else:
                        formatted_plan += f"{line}\n"
        return formatted_plan
    

    def fetch_and_parse_swagger(url):
        response = requests.get(url)
        data = json.loads(response.text)

        curl_commands = {}
        for path, path_data in data["paths"].items():
            for method, method_data in path_data.items():
                curl_command = f"curl -X {method.upper()} '{path}'"
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
    
    def get_and_display_gif(tag):
        api_key = "r8JKN0k6O6NkeFI4xRKp46jojIqvIOPD"

        # For demonstration purposes, using a fixed gif_id
        gif_id = "WAazKNEk4s0Ug"  

        response = requests.get(f"https://api.giphy.com/v1/gifs/{gif_id}?api_key={api_key}&tag={tag}&rating=g")

        if response.status_code == 200:
            gif_url = response.json()["data"]["images"]["original"]["url"]

            with requests.get(gif_url, stream=True) as r:
                if r.status_code == 200:
                    r.decode_content = True
                    with open('local_filename.gif','wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                    st.image('local_filename.gif')
                else:
                    st.error("Failed to download GIF")
        else:
            st.error("Failed to retrieve GIF")


    # Goals input container
    goals_container = st.container()
    with goals_container:
        if st.session_state.submitted_details:


            # Define a list of pages
            pages = ["Select a page", "Diet Plan Generator", "Workout Plan Generator","Ethnicity Based Recipe Generator",'Swagger to cURL Converter',"Random Gif Generator"]

            # Create a radio button in the sidebar to select the page
            selected_page = st.sidebar.radio("Navigate", pages)

            # Load the selected page
            if selected_page == "Diet Plan Generator":
                st.subheader("Diet Plan Generator")
                goals = st.multiselect(
                    "Select your diet goals:",
                    ["Weight loss", "Weight gain", "Fat loss", "Immunity Boosting", "Generate Stamina"]
                )
                preference = st.multiselect(
                    "Select your Meal Preference:",
                    ["Veg", "Non-Veg", "Both"]
                )
                progress_slot = st.empty()
                if st.button('Generate Diet Plan'):
                    if goals:
                        progress_bar = progress_slot.progress(0)
                        for percent_complete in range(0, 101, 5):
                            time.sleep(0.1)  # Adjust the sleep time as necessary
                            progress_bar.progress(percent_complete)
                        diet_plan = generate_diet_plan(goals, preference)
                        progress_bar.progress(100)
                        formatted_diet = format_diet_plan(diet_plan)
                        st.markdown(formatted_diet)
                    else:
                        st.write("Please select at least one goal to get a diet plan.")

            elif selected_page == "Workout Plan Generator":
                st.subheader("Workout Plan Generator")
                workout_level = st.selectbox(
                    "Select your workout level:",
                    ["Beginner", "Intermediate", "Advanced"]
                )
                workout_duration = st.slider("Select desired workout duration (in minutes):", 10, 120)
                progress_slot = st.empty()
                if st.button('Generate Workout Plan'):
                    # Start progress bar in the designated slot
                    progress_bar = progress_slot.progress(0)
                    for percent_complete in range(0, 101, 5):
                        time.sleep(1)  # Simulating some processing time
                        progress_bar.progress(percent_complete)

                    workout_plan = generate_workout_plan(workout_level, workout_duration)
                    # Once processing is complete, display the workout plan
                    # Reset progress bar to 100%
                    progress_bar.progress(100)

                    # Format the diet_plan for better display
                    workout_plan = format_diet_plan(workout_plan)
                    st.markdown(workout_plan)

            elif selected_page == "Ethnicity Based Recipe Generator":
                st.subheader("Ethnicity Based Recipe Generator")
                cuisines_by_ethnicity = {
                    "American": ["Fast Food", "Comfort Food", "BBQ", "Cajun", "Soul Food", "Tex-Mex", "New England"],
                    "Chinese": ["Szechuan", "Cantonese", "Hunan", "Shandong", "Fujian", "Zhejiang", "Jiangsu"],
                    "Indian": ["North Indian", "South Indian", "West Indian", "East Indian", "Rajasthani", "Punjabi", "Goan"],
                    "Italian": ["Tuscan", "Sicilian", "Lazio", "Veneto", "Lombard", "Piedmontese", "Calabrian"],
                    "Mexican": ["Oaxacan", "Veracruz", "Yucatecan", "Poblano", "Norteno", "Jalisco", "Baja"],
                    "Japanese": ["Kanto", "Kansai", "Hokkaido", "Kyushu", "Chugoku", "Tohoku", "Chubu"],
                    "Thai": ["Central Thai", "Isan", "Southern Thai", "Northern Thai", "Western Thai", "Eastern Thai", "Bangkok"]
                }
                vegnonveg = st.selectbox('Select Veg/ Non-Veg', ["Veg", "Non-Veg"], key="vegnonveg")

                # Initialize session state if not already initialized
                if "ethnicity" not in st.session_state:
                    st.session_state["ethnicity"] = list(cuisines_by_ethnicity.keys())[0]

                if "cuisine" not in st.session_state:
                    st.session_state["cuisine"] = cuisines_by_ethnicity[st.session_state["ethnicity"]][0]

                if "previous_cuisine" not in st.session_state:
                    st.session_state["previous_cuisine"] = ""

                if "ingredients" not in st.session_state:
                    st.session_state["ingredients"] = ""

                ethnicity = st.selectbox('Select Ethnicity', list(cuisines_by_ethnicity.keys()), key="ethnicity")
                cuisine = st.selectbox('Select Cuisine', cuisines_by_ethnicity[ethnicity], key="cuisine")

                # Populate Ingredients Button
                if st.button('Populate Ingredients'):
                    # Check if cuisine has changed, if so, update ingredients
                    if st.session_state.get("previous_cuisine", None) != st.session_state.get("cuisine", None):
                        st.session_state["ingredients"] = suggest_ingredients(st.session_state["cuisine"], vegnonveg)
                        if 'cuisine' in st.session_state:
                            st.session_state["previous_cuisine"] = st.session_state["cuisine"]

                # If ingredients are available, show the text area
                if st.session_state.get("ingredients", None):
                    # Just create the text area without explicitly setting the value
                    ingredients = st.text_area("Ingredients (comma-separated)", key="ingredients")
                    
                    if not ingredients:
                        ingredients = st.session_state.get("ingredients", "")
                    
                    if st.button('Generate Recipes'):
                        recipe = generate_recipe(ingredients, cuisine, vegnonveg)
                        recipie_plan = format_diet_plan(recipe)
                        st.markdown(recipie_plan)


            elif selected_page == 'Swagger to cURL Converter':
                # URL of the Swagger JSON file
                url = st.text_input('Enter Swagger URL', 'http://rackerlabs.github.io/wadl2swagger/openstack/swagger/os-qos-v2.json')

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

                All P1 and P2 cases required.  For each of these, a new row in the table would be added. Use the details provided by the user to generate each field in the table. The output should cover all the points in the test case document in a tabular format. 
                    """

                    # Execute each cURL command and collect responses
                    responses = []
                    for command in list(curl_commands.values())[:2]:
                        output, total_time = run_cmd_1(prompt_text, command)
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
                        output, total_time = run_cmd_1(prompt_text, command)
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

            elif selected_page == 'Random Gif Generator':
                # Ask the user for input
                st.subheader("Random Gif Generator")
                tag = st.text_input("Enter a tag:")


                if tag:
                    if st.button('Show GIF'):
                        get_and_display_gif(tag)

            elif selected_page == "Select a page":
                st.subheader(f"Hello {st.session_state.name}, your BMI is {st.session_state.bmi:.2f} which falls under the '{st.session_state.category}' category.")
                st.markdown("Please select a page from the sidebar to get started.")

    col1, col2 = st.columns([4,1]) 

    # Place the button in the second (right) column
    if col2.button('Logout'):
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.experimental_rerun()

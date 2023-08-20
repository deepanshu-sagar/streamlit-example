import os
import subprocess
import tempfile
import time
import streamlit as st
import sqlite3
import hashlib

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
        st.subheader("Login Section")
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
    st.title("Vellocity Fitness Studio")


    # Create some empty space below the links to ensure the rest of the content is pushed downwards
    empty_space_below = [st.empty() for _ in range(6)]

    def run_cmd(prompt_text):
        start_time = time.time()

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

    def generate_diet_plan(goals,preference):
        """Generate a diet plan based on goals using OpenAI."""
        
        if not goals:
            return "Please select at least one goal to get a diet plan."

        prompt = f"Please provide a diet plan for the following goals: {' and '.join(goals)}. Break it down into Breakfast, Lunch, and Dinner. Take note that Diet Plan is to be created as per the person is living in Pune, India and is {preference} person. Try to keep the Diet Plan Cost effective where ever possible. Do not mention this location and cost effective information in the response."
        output = run_cmd(prompt)
        return output
        
        #return completion.choices[0].message["content"]

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


    # Goals input container
    goals_container = st.container()
    with goals_container:
        if st.session_state.submitted_details:
            st.write(f"Hello {st.session_state.name}, your BMI is {st.session_state.bmi:.2f} which falls under the '{st.session_state.category}' category.")

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
                    # Start progress bar in the designated slot
                    progress_bar = progress_slot.progress(0)
                    for percent_complete in range(0, 101, 5):
                        time.sleep(1)  # Simulating some processing time, adjust as necessary
                        progress_bar.progress(percent_complete)

                    diet_plan = generate_diet_plan(goals, preference)
                    # Once processing is complete, set progress bar to 100%
                    progress_bar.progress(100)

                    # Format the diet_plan for better display
                    formatted_diet = format_diet_plan(diet_plan)
                    st.markdown(formatted_diet)

                else:
                    st.write("Please select at least one goal to get a diet plan.")



    # Create some empty space above the links to push them to the middle
    empty_space_above = [st.empty() for _ in range(6)]

    links_container = st.container()

    with links_container:
        col1, col2, col3 = st.columns([3,6,1])

        with col2:
            st.markdown("#### Connect with us:")
            st.markdown(
                '<a href="https://www.google.com/search?hl=en-GB&authuser=1&sxsrf=ALiCzsbjhjaoDzymXxMbxDvj1nf9M7MUxA:1652284809105&q=Vellocity+Fitness+Studio&ludocid=13157170914602917019&gsas=1&lsig=AB86z5X5G3Gg3L9SuiBF_TQ0YG9k&kgs=29295f080505f34d&shndl=-1&source=sh/x/kp/local/2&" target="_blank">📞 Google Reviews</a>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<a href="https://wa.me/+91-9766623660" target="_blank">📞 WhatsApp Us</a>',
                unsafe_allow_html=True,
            )
            
            st.markdown(
                '<a href="https://www.instagram.com/artteeofficial/" target="_blank">👕 Artteeofficial Instagram</a>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<a href="https://www.instagram.com/Vellocityfndstudio/" target="_blank">📷 Vellocity Fitness Studio Instagram</a>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<a href="https://www.google.com/maps/place/Vellocity+Fitness+Studio/@18.6002561,73.7641115,15z/data=!4m6!3m5!1s0x3bc2b96e6f27c2df:0xb697a93cb6021c9b!8m2!3d18.6002561!4d73.7641115!16s%2Fg%2F11f15m5lzj?hl=en-GB&entry=ttu" target="_blank">👕 Vellocity Fitness Studio Maps</a>',
                unsafe_allow_html=True,
            )

    if st.button('Logout'):
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.experimental_rerun()

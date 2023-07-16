"""
This is a Python script that serves as a frontend for a conversational AI model built with the `langchain` and `llms` libraries.
The code creates a web application using Streamlit, a Python library for building interactive web apps.
"""

# Import necessary libraries
import streamlit as st
from PIL import Image
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationEntityMemory
from langchain.chains.conversation.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
import re
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA

def is_four_digit_number(string):
    pattern = r'^\d{4}$'  # Matches exactly four digits
    return bool(re.match(pattern, string))


# Set Streamlit page configuration

st.set_page_config(page_title=' 🤖ChatGPT with Memory🧠', layout='wide')
# Initialize session states
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []
if "just_sent" not in st.session_state:
    st.session_state["just_sent"] = False
if "temp" not in st.session_state:
    st.session_state["temp"] = ""
if "balance" not in st.session_state:
    st.session_state["balance"] = 0.0
if "deposit" not in st.session_state:
    st.session_state["deposit"] = 3.0

def clear_text():
    st.session_state["temp"] = st.session_state["input"]
    st.session_state["input"] = ""


# Define function to get user input
def get_text():
    """
    Get the user input text.

    Returns:
        (str): The text entered by the user
    """
    input_text = st.text_input("You: ", st.session_state["input"], key="input", 
                            placeholder="Your AI assistant here! Ask me anything ...", 
                            on_change=clear_text,    
                            label_visibility='hidden')
    input_text = st.session_state["temp"]
    return input_text




    # Define function to start a new chat
def new_chat():
    """
    Clears session state and starts a new chat.
    """
    save = []
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        save.append("User:" + st.session_state["past"][i])
        save.append("Bot:" + st.session_state["generated"][i])        
    st.session_state["stored_session"].append(save)
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["input"] = ""
    st.session_state.entity_memory.store = {}
    st.session_state.entity_memory.buffer.clear()

#Set up sidebar with various options
# with st.sidebar.expander("🛠️ ", expanded=False):
#    # Option to preview memory store
#    if st.checkbox("Preview memory store"):
#        with st.expander("Memory-Store", expanded=False):
#            st.session_state.entity_memory.store
#    # Option to preview memory buffer
#    if st.checkbox("Preview memory buffer"):
#        with st.expander("Bufffer-Store", expanded=False):
#            st.session_state.entity_memory.buffer
#    MODEL = st.selectbox(label='Model', options=['gpt-3.5-turbo','text-davinci-003','text-davinci-002','code-davinci-002'])
#    K = st.number_input(' (#)Summary of prompts to consider',min_value=3,max_value=1000)

MODEL = "gpt-3.5-turbo"
K = 100

with st.sidebar:
    st.markdown("---")
    st.markdown("# About")
    st.markdown(
       "ChatGPTm is ChatGPT added memory. "
       "It can do anything you asked and also remember you."
            )

    
# Set up the Streamlit app layout
st.title("🤖 ChatGPT with Memory 🧠")
#st.subheader(" Powered by 🦜 LangChain + OpenAI + Streamlit")

hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

# Let user select version
st.write("GPT4.0")
version = st.selectbox("Choose ChatGPT version ", ("3.5", "4.0"))
if version == "3.5":
    # Use GPT-3.5 model
    MODEL = "gpt-3.5-turbo"
else:
    # USe GPT-4.0 model
    MODEL = "gpt-4"
    
# Ask the user to enter their OpenAI API key
#API_O = st.sidebar.text_input("API-KEY", type="password")
# Read API from Streamlit secrets
# API_O = os.getenv("OPENAI_API_KEY")
API_O = st.text_input('OpenAI API Key', type='password')

# Session state storage would be ideal
if API_O:
    # Create an OpenAI instance
    llm = OpenAI(temperature=0,
                openai_api_key=API_O, 
                model_name=MODEL, 
                verbose=False) 


    # Create a ConversationEntityMemory object if not already created
    if 'entity_memory' not in st.session_state:
            st.session_state.entity_memory = ConversationEntityMemory(llm=llm, k=K )
        
        # Create the ConversationChain object with the specified configuration
    Conversation = ConversationChain(
            llm=llm, 
            prompt=ENTITY_MEMORY_CONVERSATION_TEMPLATE,
            memory=st.session_state.entity_memory
        )  
else:
    st.sidebar.warning('API key required to try this app.The API key is not stored in any form.')
    # st.stop()


# Add a button to start a new chat
#st.sidebar.button("New Chat", on_click = new_chat, type='primary')

# Get the user input
user_input = get_text()

# Generate the output using the ConversationChain object and the user input, and add the input/output to the session
if user_input:
    if st.session_state["balance"] > -0.03:
        with get_openai_callback() as cb:
            output = Conversation.run(input=user_input)  
            st.session_state.past.append(user_input)  
            st.session_state.generated.append(output) 
            st.session_state["balance"] -= cb.total_cost * 4
    else:
        st.session_state.past.append(user_input)  
        if is_four_digit_number(user_input) :
            st.session_state["balance"] += st.session_state["deposit"]
            st.session_state.generated.append("谢谢支付，你可以继续使用了") 
        else: 
            st.session_state.generated.append("请用下面的支付码支付¥10后才可以再继续使用。我会再送你¥10元。支付时请记下转账单号的最后4位数字，在上面对话框输入这四位数字") 
        

# Allow to download as well
download_str = []
# Display the conversation history using an expander, and allow the user to download it
with st.expander("Conversation", expanded=True):
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        st.info(st.session_state["past"][i],icon="🧐")
        st.success(st.session_state["generated"][i], icon="🤖")
        download_str.append(st.session_state["past"][i])
        download_str.append(st.session_state["generated"][i])
                            
    # Can throw error - requires fix
    download_str = '\n'.join(download_str)
    
    if download_str:
        st.download_button('Download 下载',download_str)

# Display stored conversation sessions in the sidebar
for i, sublist in enumerate(st.session_state.stored_session):
        with st.sidebar.expander(label= f"Conversation-Session:{i}"):
            st.write(sublist)

# Allow the user to clear all stored conversation sessions
if st.session_state.stored_session:   
    if st.sidebar.checkbox("Clear-all"):
        del st.session_state.stored_session
        
def generate_response(uploaded_file, openai_api_key, query_text):
    # Load document if file is uploaded
    if uploaded_file is not None:
        documents = [uploaded_file.read().decode()]
        # Split documents into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.create_documents(documents)
        # Select embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        # Create a vectorstore from documents
        db = Chroma.from_documents(texts, embeddings)
        # Create retriever interface
        retriever = db.as_retriever()
        # Create QA chain
        qa = RetrievalQA.from_chain_type(llm=OpenAI(openai_api_key=openai_api_key), chain_type='stuff', retriever=retriever)
        return qa.run(query_text)


st.title('🦜🔗 Use below For Ask the Doc App')

# File upload
uploaded_file = st.file_uploader('Upload an article', type='txt')
# Query text
query_text = st.text_input('Enter your question:', placeholder = 'Please provide a short summary.', disabled=not uploaded_file)

# Form input and query
result = []
with st.form('myform', clear_on_submit=True):
    openai_api_key = API_O
    submitted = st.form_submit_button('Submit', disabled=not(uploaded_file and query_text))
    if submitted and openai_api_key.startswith('sk-'):
        with st.spinner('Calculating...'):
            response = generate_response(uploaded_file, openai_api_key, query_text)
            result.append(response)
            del openai_api_key

if len(result):
    st.info(response)


st.title('🦜🔗 Bito')

import streamlit as st
import subprocess
import time
import tempfile
import os

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


prompt_text = st.text_area("Prompt Text", "Entry Your Prompt Text Here")
uploaded_file = st.file_uploader("Choose a txt file... ask anything about the file.", type="txt")

if uploaded_file is not None:
    pyfile_text = uploaded_file.read().decode()

if st.button('Submit'):
    fetching_message = st.empty()
    fetching_message.text("Fetching response...")
    output, total_time = run_cmd(prompt_text, pyfile_text)
    fetching_message.empty()
    st.text_area("Command Output", output.decode('utf-8'), height=200)
    st.write(f'Total time taken: {total_time} seconds')


st.title('🦜🔗 Bito with memory')

import streamlit as st
import tempfile

def clear_runcontext():
    with open("runcontext.txt", "w") as f:
        f.write('')

def run_cmd(inventory_text, prompt_text):

    inventory_fd = 'temp_inventory.txt'
    prompt_fd = 'temp_prompt_fd.txt'
    testdata_path = 'temp_testdata.txt'

    with open(inventory_fd, 'w') as inventory_file:
        inventory_file.write(inventory_text)
        
    with open(prompt_fd, 'w') as prompt_file:
        prompt_file.write(prompt_text)
        
    with open(testdata_path, 'w') as inventory_file:
        inventory_file.write('')

    cmd = ["type" if os.name == 'nt' else "cat", inventory_fd, "|", "bito", "-c", "runcontext.txt", "-p", prompt_fd, ">", testdata_path]
    print (cmd)
    subprocess.check_output(cmd, shell=True)

    with open(testdata_path, 'r') as testdata_file:
        output = testdata_file.read()

    return output


if 'inventory_text' not in st.session_state:
    st.session_state.inventory_text = ''

if 'prompt_text' not in st.session_state:
    st.session_state.prompt_text = 'Ask Anything...'

inventory_text = st.text_area("Initial Text If Any... I'll Keep it in memory", st.session_state.inventory_text)
prompt_text = st.text_area("Prompt", st.session_state.prompt_text)

if st.button('Submit', key='submit_new'):
    output = run_cmd(inventory_text, prompt_text)
    st.text_area("Command Output", output, height=200)

if st.button('Clear Memory', key='clear_memory'):
    clear_runcontext()


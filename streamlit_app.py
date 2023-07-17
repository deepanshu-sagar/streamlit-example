# Import necessary libraries
import streamlit as st
from PIL import Image
import os
import tempfile
from langchain.chains import ConversationChain, RetrievalQA
from langchain.chains.conversation.memory import ConversationEntityMemory
from langchain.chains.conversation.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain


def generate_response(openai_api_key, query_text, uploaded_file):
    documents = [uploaded_files.read().decode('utf-8')]

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    docs = text_splitter.create_documents(documents)
    
    # Select embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    persist_directory = "chroma_db"

    # Create a vectorstore from documents
    db = Chroma.from_documents(docs, embeddings,persist_directory=persist_directory)

    db.persist()

    # Create QA chain
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', openai_api_key=openai_api_key, temperature=0)
    chain = load_qa_chain(llm=llm, chain_type='stuff')
    matching_docs_score = db.similarity_search_with_score(query_text)

    if len(matching_docs_score) == 0:
        raise Exception("No matching documents found")

    matching_docs = [doc for doc, score in matching_docs_score]
    answer = chain.run(input_documents=matching_docs, question=query_text)

    sources = [{
        "content": doc.page_content,
        "metadata": doc.metadata,
        "score": score
    } for doc, score in matching_docs_score]

    return answer, sources
    

st.title('🦜🔗 Use below For Ask the Doc App')

# OpenAI API Key
API_O = st.text_input('OpenAI API Key', type='password')

# File upload
uploaded_files = st.file_uploader('Upload an article', type='txt')

# Query text
query_text = st.text_input('Enter your question:', placeholder='Please provide a short summary.', disabled=not uploaded_files)


prompt_template = "ads_txt_crawled_data has data having pubmatic.com entries in ads.txt "+ query_text # Replace this with your own template
formatted_query_text = prompt_template.format(query_text)

# Form input and query
result = []
with st.form('myform', clear_on_submit=True):
    openai_api_key = API_O
    submitted = st.form_submit_button('Submit', disabled=not(uploaded_files and formatted_query_text))
    if submitted and openai_api_key.startswith('sk-'):
        with st.spinner('Calculating...'):
            response, sources = generate_response(openai_api_key, formatted_query_text, uploaded_files)
            result.append(response)
            del openai_api_key

if len(result):
    st.info(response)

from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
import subprocess
import tempfile
from langchain.llms import OpenAI
from typing import Any, Dict

class Input(BaseModel):
    prompt: str
    featureName: str

def run_cmd(prompt_text):
    with tempfile.NamedTemporaryFile(mode='w+') as temp:
        print (prompt_text)
        temp.write(prompt_text)
        temp.seek(0)
        cmd = ["cat", temp.name, "|", "bito"]
        print (cmd)
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return output

def prompt_to_query_new(prompt: str, info: str, data: str):
    template = """
    Your mission is convert SQL query from given {prompt}. Use following database information for this purpose (info key is a database column name and info value is explanation) : {info} .  along with this i am sharing some sample data from this table :  {data}
    --------
    Put your query in the  JSON structure with key name is 'query'
    """
    final_prompt = template.format(prompt=prompt, info=info, data=data)
    output = run_cmd(final_prompt)
    return output

def read_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        data = file.read()
    return data

app = FastAPI()

@app.post("/process")
async def process(input: Input):
    info = read_file( f"{input.featureName}_info.json")
    data = read_file( f"{input.featureName}_data.txt")
    query = prompt_to_query_new(input.prompt, info, data)
    return {"Generated SQL Query": query}

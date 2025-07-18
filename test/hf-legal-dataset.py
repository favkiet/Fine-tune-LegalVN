import datasets
from huggingface_hub import login
from dotenv import load_dotenv
import os
import pandas as pd


# Dataset Description

# Dataset Name: Vietnamese Law and Ethics Multiple-Choice Questions (VLEMCQ)
# Author: Dung Nguyen Quang License: Apache license 2.0 Language: Vietnamese
# Task: Multiple-Choice Question Answering (MCQA)
# Domain: Law, Ethics, and Social Responsibility

# Load .env and get API key
load_dotenv()
hf_api_key = os.getenv("HF_API_KEY")
if hf_api_key:
    login(token=hf_api_key)
else:
    print("HF_API_KEY not found in environment variables. Skipping login.")

# Load the Vietnamese Legal QA dataset from Hugging Face
data = datasets.load_dataset("nqdhocai/vietnamese-legal-qa")
df = data['train'].to_pandas()

# Extract the actual answer text from options
def extract_answer_text(row):
    options = row['options'].split('\n')
    option_dict = {}
    for opt in options:
        if '.' in opt:
            key, val = opt.split('.', 1)
            option_dict[key.strip()] = val.strip()
    answer_key = row.get('answer')
    if answer_key:
        return option_dict.get(answer_key.strip(), '')
    return ''  # fallback if answer is None or not found

# Apply function to extract answer text
df['answer_text'] = df.apply(extract_answer_text, axis=1)

# Rename columns
df.rename(columns={
    'id': 'id',
    'question': 'question',
    'answer': 'answer_choice',
    'options': 'options',
    'answer_text': 'answer'
}, inplace=True)

# Save the processed DataFrame to a CSV file
df.to_csv('data/processed/vlemvq.csv', index=False)


# ================
data = datasets.load_dataset("phamson02/large-vi-legal-queries")
df = data['train'].to_pandas()
df.rename(columns={'query': 'question'}, inplace=True)
df.to_csv('data/processed/large-vi-legal-queries.csv', index=False)
print(df.head())


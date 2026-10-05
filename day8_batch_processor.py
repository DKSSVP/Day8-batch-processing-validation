import os
import json
import re
import requests

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SHEETDB_API_URL = os.getenv("SHEETDB_API_URL")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

raw_profiles = [
    "Prathyusha | Email: prathyusha@craftechco.com | Role: Chief Executive Officer",
    "Mohan Krishna | Email: mohan.krishna@craftechco.com | Role: Chief Technology Officer",
    "Divakar ch | Email: divakar.ch@craftechco.com | Role: HR Manager",
    "Sai Prasanna | Email: sai.prasanna@craftechco.com | Role: HR Executive",
    "Sudheer | Email: sudheer@craftechco.com | Role: Scrum Master",
    "Akhila K | Email: akhila.k@craftechco.com | Role:  Lead Gen AI Specialist",
    "Ravi Kiran | Email: ravi.kiran@craftechco.com | Role: Lead Gen AI Specialist",
    "Damodhara Prasad | Email: damodhara.prasad@craftechco.com | Role: Gen AI Specialist",
    "Ravi Teja | Email: ravi.teja@craftechco.com | Role: Gen AI Specialist",
    "Karthik Reddy | Email: karthik.reddy@craftechco.com | Role: Sales Executive",
    "Siva Prasad | Email: | Role: Sales Executive",
    "Soundarya K | Email: soundarya.k@craftechco.com | Role: SAP Consultant",
    "Srinivas Reddy | Email: | Role: SAP Consultant"
]

def extract_profile_to_json(profile_text):
    prompt = f"""
Extract the candidate information from the profile below.

Return one valid JSON object with exactly these fields:
Name
Email
Role

Rules:
- Return JSON only.
- Do not use Markdown code fences.
- Do not add explanations.
- Use only information available in the profile.
- Do not invent information.

Profile:
{profile_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o",
        max_tokens=100,
        messages=[
            {
                "role": "system",
                "content": "You are a candidate profile extraction assistant. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

def parse_profile_json(raw_output):
    try:
        return json.loads(raw_output)

    except json.JSONDecodeError as error:
        print("JSON parsing failed.")
        print("Error:", error)
        return None

def validate_record(record):
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    if not record.get("Name") or len(record.get("Name")) < 2:
        return False

    if not re.match(email_pattern, record.get("Email", "")):
        return False

    return True

def process_batch(profiles):
    valid_batch = []

    for profile in profiles:
        print("\nProcessing profile:")
        print(profile)

        raw_output = extract_profile_to_json(profile)

        record = parse_profile_json(raw_output)

        if record is None:
            print("Record skipped because JSON parsing failed.")
            continue

        if validate_record(record):
            valid_batch.append(record)
            print("Validation successful.")
            print("Record added to valid batch.")
        else:
            print("Validation failed.")
            print("Record skipped.")

    return valid_batch

def push_batch_to_sheetdb(valid_batch):
    payload = {
        "data": valid_batch
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(
        SHEETDB_API_URL,
        json=payload,
        headers=headers,
        timeout=10
    )

    return response

print("----- Batch Processing Started -----")

valid_batch = process_batch(raw_profiles)

print("\n----- Batch Processing Result -----")
print("Valid records:", len(valid_batch))

if valid_batch:
    print("\n----- SheetDB Bulk Insertion -----")

    response = push_batch_to_sheetdb(valid_batch)

    print("HTTP Status Code:", response.status_code)

    if response.status_code == 201:
        print(f"{len(valid_batch)} candidate records added successfully.")
    else:
        print("SheetDB request failed.")
        print("Response:", response.text)

else:
    print("No valid records to insert.")


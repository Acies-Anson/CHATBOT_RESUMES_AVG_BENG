import requests
import json
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL=os.getenv("MODEL_NAME")
# First API call with reasoning

def call_openrouter(prompt):
    response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    data=json.dumps({
        "model": MODEL,
        "messages": [
            {
            "role": "user",
            "content": "How many r's are in the word 'strawberry'?"
            }
        ],
        "reasoning": {"enabled": True}
    })
    )

    # Extract the assistant message with reasoning_details
    response = response.json()
    print("FULL API RESPONSE:")
    print(response)
    
    if "choices" not in response:
        return "⚠️ API failed — check terminal."
    message = response['choices'][0]['message']
    # Preserve the assistant message with reasoning_details
    messages = [
    {"role": "user", "content": "How many r's are in the word 'strawberry'?"},
    {
        "role": "assistant",
        "content":message.get('content'),
        "reasoning_details": response.get('reasoning_details')  # Pass back unmodified
    },
    {"role": "user", "content": "Are you sure? Think carefully."}
    ]
    return message.get("content")
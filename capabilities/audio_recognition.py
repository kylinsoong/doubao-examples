import os
import requests
import time
import json

# API Endpoints
SUBMIT_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
QUERY_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"

# Read API keys from system environment variables
API_APP_KEY = os.getenv("DOUBAO_API_APP_KEY")
API_ACCESS_KEY = os.getenv("DOUBAO_API_ACCESS_KEY")
API_RESOURCE_ID = os.getenv("DOUBAO_API_RESOURCE_ID")
API_SEQUENCE = os.getenv("DOUBAO_API_SEQUENCE", "-1")  # Default to "-1"

# Validate environment variables
if not all([API_APP_KEY, API_ACCESS_KEY, API_RESOURCE_ID]):
    raise EnvironmentError("Environment variables DOUBAO_API_APP_KEY, DOUBAO_API_ACCESS_KEY, and DOUBAO_API_RESOURCE_ID must be set.")

# Submit API function
def submit_task(payload_file):
    # Load payload from file
    with open(payload_file, 'r') as file:
        payload = json.load(file)

    # Headers for the Submit API
    headers = {
        "Content-Type": "application/json",
        "X-Api-App-Key": API_APP_KEY,
        "X-Api-Access-Key": API_ACCESS_KEY,
        "X-Api-Resource-Id": API_RESOURCE_ID,
        "X-Api-Request-Id": "",  # Can be dynamically generated if needed
        "X-Api-Sequence": API_SEQUENCE,
    }

    # Send POST request to the Submit API
    response = requests.post(SUBMIT_URL, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            print("Task submitted successfully!")
            print(f"Request ID: {data['data']['Request-Id']}")
            return data["data"]["Request-Id"]
        else:
            print(f"Submit API Error: {data.get('message')}")
            return None
    else:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
        return None

# Query API function
def query_task(request_id):
    # Headers for the Query API
    headers = {
        "Content-Type": "application/json",
        "X-Api-App-Key": API_APP_KEY,
        "X-Api-Access-Key": API_ACCESS_KEY,
        "X-Api-Resource-Id": API_RESOURCE_ID,
        "X-Api-Request-Id": request_id,
    }

    # Send POST request to the Query API
    while True:
        response = requests.post(QUERY_URL, headers=headers, json={})
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                status = data["data"]["status"]
                print(f"Task Status: {status}")
                if status == "completed":
                    print("Task Result:", data["data"]["result"])
                    break
                elif status == "failed":
                    print("Task failed.")
                    break
            else:
                print(f"Query API Error: {data.get('message')}")
                break
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            break

        # Wait before retrying
        time.sleep(5)

# Main function
if __name__ == "__main__":
    # Path to the payload file
    payload_file = "payload.json"  # Replace with your actual payload file path

    # Submit task
    request_id = submit_task(payload_file)
    if request_id:
        # Query task status
        query_task(request_id)


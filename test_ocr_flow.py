import requests
import time
import os

API_URL = "http://localhost:8000/api"
USERNAME = "testuser"
PASSWORD = "testpassword123"
EMAIL = "testuser@example.com"

def register():
    print(f"Registering user {USERNAME}...")
    response = requests.post(f"{API_URL}/auth/register", json={
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD,
        "is_admin": "false"
    })
    if response.status_code == 200:
        print("Registration successful")
    elif response.status_code == 400 and "already registered" in response.text:
        print("User already registered")
    else:
        print(f"Registration failed: {response.text}")
        exit(1)

def login():
    print(f"Logging in as {USERNAME}...")
    response = requests.post(f"{API_URL}/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    if response.status_code == 200:
        print("Login successful")
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        exit(1)

def upload_document(token, file_path):
    print(f"Uploading {file_path}...")
    headers = {"Authorization": f"Bearer {token}"}
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_URL}/documents/upload", headers=headers, files=files)
    
    if response.status_code == 200:
        doc = response.json()
        print(f"Upload successful. Document ID: {doc['id']}")
        return doc['id']
    else:
        print(f"Upload failed: {response.text}")
        exit(1)

def check_status(token, doc_id):
    print(f"Checking status for document {doc_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    for i in range(30):  # Wait up to 30 seconds
        response = requests.get(f"{API_URL}/documents/{doc_id}", headers=headers)
        if response.status_code == 200:
            doc = response.json()
            status = doc['status']
            print(f"Status: {status}")
            if status == "completed":
                print("Processing completed!")
                return doc
            elif status == "failed":
                print("Processing failed!")
                return doc
        else:
            print(f"Failed to get document: {response.text}")
        
        time.sleep(1)
    
    print("Timeout waiting for processing")
    return None

def main():
    register()
    token = login()
    
    file_path = "ocr/example.pdf"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        exit(1)
        
    doc_id = upload_document(token, file_path)
    result = check_status(token, doc_id)
    
    if result:
        print("\nDocument details:")
        print(f"ID: {result['id']}")
        print(f"Filename: {result['original_filename']}")
        print(f"Status: {result['status']}")
        # We could also check preview content if needed

if __name__ == "__main__":
    main()

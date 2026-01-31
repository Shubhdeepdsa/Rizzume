print("Starting verification script...", flush=True)
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8002"
# Assuming environment variables for test user, else prompt or hardcode for this quick test
EMAIL = os.getenv("TEST_EMAIL", "shub.isc.22@gmail.com") 
PASSWORD = os.getenv("TEST_PASSWORD", "1234567890")

import secrets

def get_token():
    # Try login first
    url = f"{API_URL}/auth/login"
    payload = {"email": EMAIL, "password": PASSWORD}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()["token"]
    except:
        pass

    # If login fails, try to create a temp user
    print("   Login failed, creating temp user...")
    random_suffix = secrets.token_hex(4)
    temp_email = f"test_{random_suffix}@example.com"
    temp_pass = "password123"
    
    # Signup
    signup_url = f"{API_URL}/auth/signup"
    signup_payload = {"email": temp_email, "password": temp_pass, "name": "Test User"}
    try:
        s_resp = requests.post(signup_url, json=signup_payload)
        s_resp.raise_for_status()
        print(f"   Created temp user: {temp_email}")
        
        # Login again
        l_resp = requests.post(url, json={"email": temp_email, "password": temp_pass})
        l_resp.raise_for_status()
        return l_resp.json()["token"]
    except Exception as e:
        print(f"   Signup/Login failed: {e}")
        return None

def test_resume_search(token):
    print("\n--- Testing Resume Search ---")
    url = f"{API_URL}/api/resumes/search"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. No filters (should return all, max 500)
    print("1. Search (No filters)...")
    resp = requests.post(url, json={}, headers=headers)
    if resp.status_code == 200:
        items = resp.json()
        print(f"   Success! Got {len(items)} resumes.")
    else:
        print(f"   Failed: {resp.status_code} - {resp.text}")

    # 2. Name filter
    print("2. Search (Name contains 'Resume')...")
    resp = requests.post(url, json={"name_contains": "Resume"}, headers=headers)
    if resp.status_code == 200:
         print(f"   Success! Got {len(resp.json())} resumes.")
    else:
         print(f"   Failed: {resp.text}")

def test_jd_search(token):
    print("\n--- Testing JD Search ---")
    url = f"{API_URL}/api/jds/search"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("1. Search (No filters)...")
    resp = requests.post(url, json={}, headers=headers)
    if resp.status_code == 200:
        items = resp.json()
        print(f"   Success! Got {len(items)} JDs.")
    else:
        print(f"   Failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    token = get_token()
    if token:
        test_resume_search(token)
        test_jd_search(token)

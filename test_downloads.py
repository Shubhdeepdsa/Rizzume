import httpx
import os
from dotenv import load_dotenv

# Load env but primarily assume local defaults
load_dotenv()

API_URL = "http://localhost:8000"
USERNAME = os.getenv("TEST_USER_EMAIL", "test@example.com") # Adjust if needed
PASSWORD = os.getenv("TEST_USER_PASS", "password123") 

async def main():
    async with httpx.AsyncClient(base_url=API_URL) as client:
        # 1. Register/Login
        email = f"test_{os.urandom(4).hex()}@example.com"
        password = "password123"
        print(f"Creating test user {email}...")
        
        try:
            # Register
            reg_resp = await client.post("/auth/signup", json={"email": email, "password": password, "name": "Test User"})
            if reg_resp.status_code not in [200, 201]: # 201 is typical for creation
                 # Fallback to login if already exists (unlikely with random)
                 pass
            
            # Login
            print(f"Logging in...")
            resp = await client.post("/auth/login", json={"email": email, "password": password})
            if resp.status_code != 200:
                print(f"Login failed: {resp.status_code} {resp.text}")
                return
            
            token = resp.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("Login success.")

            # Need to upload a resume first if we just created a user?
            # Yes, new user has no data.
            # We should upload a dummy resume.
            print("Uploading dummy resume...")
            dummy_pdf = b"%PDF-1.5 ... dummy content ..."
            files = {'file': ('test_resume.pdf', dummy_pdf, 'application/pdf')}
            # We also need to extract text... backend does that.
            # But the backend expects PDF usually.
            # Let's try uploading a text file as resume if allowed? backend `read_text_from_upload` handles pdf/docx/txt.
            
            files = {'file': ('test.txt', b"Unknown Resume Content", 'text/plain')}
            # Add tags as form data
            data = {'tags': '[]'}
            up_resp = await client.post("/api/resumes", headers=headers, files=files, data=data) 
            
            if up_resp.status_code != 200:
                print(f"Upload failed: {up_resp.text}")
            else:
                print("Dummy resume uploaded.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Setup error: {repr(e)}")
            return

        # 2. List Resumes
        print("\nListing Resumes...")
        resumes_resp = await client.get("/api/resumes", headers=headers)
        if resumes_resp.status_code != 200:
            print(f"Failed to list resumes: {resumes_resp.text}")
        else:
            resumes = resumes_resp.json()
            if resumes:
                resume = resumes[0]
                rid = resume["id"]
                print(f"Found resume: {resume['name']} ({rid})")
                
                # 3. Download Resume
                print(f"Downloading resume {rid}...")
                dl_resp = await client.get(f"/api/resumes/{rid}/download", headers=headers)
                if dl_resp.status_code == 200:
                    print(f"✅ Resume download success! Size: {len(dl_resp.content)} bytes")
                    print(f"Content-Type: {dl_resp.headers.get('content-type')}")
                else:
                    print(f"❌ Resume download failed: {dl_resp.status_code} {dl_resp.text}")
            else:
                print("No resumes found to test.")

        # 4. List JDs
        print("\nListing JDs...")
        jds_resp = await client.get("/api/jds", headers=headers)
        if jds_resp.status_code != 200:
            print(f"Failed to list JDs: {jds_resp.text}")
        else:
            jds = jds_resp.json()
            if jds:
                jd = jds[0]
                jid = jd["id"]
                print(f"Found JD: {jd['role_name']} ({jid})")
                
                # 5. Download JD
                print(f"Downloading JD {jid}...")
                dl_resp = await client.get(f"/api/jds/{jid}/download", headers=headers)
                if dl_resp.status_code == 200:
                    print(f"✅ JD download success! Size: {len(dl_resp.content)} bytes")
                    print(f"Content-Type: {dl_resp.headers.get('content-type')}")
                else:
                    print(f"❌ JD download failed: {dl_resp.status_code} {dl_resp.text}")
            else:
                print("No JDs found to test.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

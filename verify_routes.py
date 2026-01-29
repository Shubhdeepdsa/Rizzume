import asyncio
import sys
import os
import httpx

# Adjust path to find app
sys.path.append(os.getcwd())

from app.service.pocketbase import get_pocketbase_service

async def verify_routes():
    pb = get_pocketbase_service()
    email = "test_tag_user@example.com"
    password = "password123"
    
    try:
        # Login
        try:
            auth = await pb.auth_with_password(email, password)
            token = auth["token"]
            user_id = auth["record"]["id"]
        except:
             # Create user if missing (might fail if already deleted)
             await pb.create_user(email, password, "Test Tag User")
             auth = await pb.auth_with_password(email, password)
             token = auth["token"]
             user_id = auth["record"]["id"]

        print(f"Authenticated. Token: {token[:10]}...")
        
        # We need to test via HTTP requests ideally to verify ROUTING.
        # Calling PB service methods only tests the service, not the route prefix.
        # So I will use httpx to hit the FASTAPI app.
        # But the app is running? 
        # The user's dev server is running on 8090 maybe?
        # Actually I can't hit the user's running process easily unless I know port.
        # But I can restart the dev server or assume it auto-reloads.
        # The user has ./dev.sh running. It auto-reloads.
        # So I can just curl or use python httpx to hit localhost.
        
        # Default port for FastAPI in this project?
        # main.py doesn't show run command, usually uvicorn default 8000.
        # dev.sh usually runs uvicorn.
        
        # Let's try to hit http://127.0.0.1:8000/api/resume/tags and /api/jd/tags
        # If port is different I might fail.
        # dev.sh usually sets port.
        # I'll try 8000.
        
        base_url = "http://127.0.0.1:8001" # Testing on my custom port
        
        async with httpx.AsyncClient(base_url=base_url, timeout=5) as client:
            headers = {"Authorization": f"Bearer {token}"}
            
            print(f"Testing {base_url}/api/resume/tags ...")
            r1 = await client.get("/api/resume/tags", headers=headers)
            print(f"Status: {r1.status_code}")
            if r1.status_code == 200:
                print("✅ Resume Tags Route Works")
            else:
                 print(f"❌ Resume Tags Route Failed. Response: {r1.text}")
                 
            print(f"Testing {base_url}/api/jd/tags ...")
            r2 = await client.get("/api/jd/tags", headers=headers)
            print(f"Status: {r2.status_code}")
            if r2.status_code == 200:
                print("✅ JD Tags Route Works")
            else:
                 print(f"❌ JD Tags Route Failed. Response: {r2.text}")
                 
    except Exception as e:
        print(f"Verification Failed: {e}")
    finally:
        await pb.close()

if __name__ == "__main__":
    asyncio.run(verify_routes())

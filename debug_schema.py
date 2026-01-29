import asyncio
import logging
from app.service.pocketbase import get_pocketbase_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_schema():
    pb = get_pocketbase_service()
    
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    admin_email = os.getenv("PB_ADMIN_EMAIL", "shubhdeepdas0@gmail.com") 
    admin_pass = os.getenv("PB_ADMIN_PASSWORD", "030301@Deepdas")
    
    try:
        token = await pb.admin_auth_with_email(admin_email, admin_pass)
        logger.info("✅ Authenticated as Admin")
        
        # Get Collection
        r = await pb.client.get("/api/collections/job_descriptions", headers={"Authorization": f"Bearer {token}"})
        if r.is_success:
            data = r.json()
            fields = data.get("fields", data.get("schema", []))
            for f in fields:
                if f["name"] == "tags":
                    logger.info("Found 'tags' field:")
                    logger.info(f)
                    val = f.get("maxSelect")
                    logger.info(f"maxSelect: {val}")
        else:
            logger.error(f"Failed to fetch schema: {r.text}")
            
    except Exception as e:
        logger.error(e)
    finally:
        await pb.close()

if __name__ == "__main__":
    asyncio.run(check_schema())

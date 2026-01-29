import json
from typing import Dict, Any, List

def get_resume_tags_schema(users_collection_id: str = "_pb_users_auth_") -> Dict[str, Any]:
    return {
        "name": "resume_tags",
        "type": "base",
        "fields": [
            {
                "name": "user",
                "type": "relation",
                "required": True,
                "collectionId": users_collection_id,
                "cascadeDelete": False,
                "maxSelect": 1,
            },
            {
                "name": "label",
                "type": "text",
                "required": True,
            },
            {
                "name": "created",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": False,
            },
            {
                "name": "updated",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": True,
            }
        ],
        "listRule": "user = @request.auth.id",
        "viewRule": "user = @request.auth.id",
        "createRule": "@request.auth.id != '' && user = @request.auth.id",
        "updateRule": "user = @request.auth.id",
        "deleteRule": "user = @request.auth.id",
        "indexes": [
            "CREATE UNIQUE INDEX idx_user_label ON resume_tags (user, label)"
        ]
    }

def get_resumes_schema(users_collection_id: str = "_pb_users_auth_", tags_collection_id: str = "resume_tags") -> Dict[str, Any]:
    return {
        "name": "resumes",
        "type": "base",
        "fields": [
            {
                "name": "user",
                "type": "relation",
                "required": True,
                "collectionId": users_collection_id,
                "cascadeDelete": False,
                "maxSelect": 1,
            },
            {
                "name": "name",
                "type": "text",
                "required": True,
            },
            {
                "name": "file",
                "type": "file",
                "required": False,
                "maxSelect": 1,
                "maxSize": 5242880,
                "mimeTypes": ["application/pdf", "text/plain"],
            },
            {
                "name": "original_text",
                "type": "text",
                "required": False,
            },
            {
                "name": "tags",
                "type": "relation",
                "required": False,
                "collectionId": tags_collection_id,
                "cascadeDelete": False,
                "maxSelect": 0, # Unlimited
            },
            {
                "name": "embeddings",
                "type": "json",
                "required": False,
            },
            {
                "name": "created",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": False,
            },
            {
                "name": "updated",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": True,
            }
        ],
        "listRule": "user = @request.auth.id",
        "viewRule": "user = @request.auth.id",
        "createRule": "@request.auth.id != '' && user = @request.auth.id",
        "updateRule": "user = @request.auth.id",
        "deleteRule": "user = @request.auth.id",
    }

def get_jds_schema(users_collection_id: str = "_pb_users_auth_") -> Dict[str, Any]:
    return {
        "name": "job_descriptions",
        "type": "base",
        "fields": [
            {
                "name": "user",
                "type": "relation",
                "required": True,
                "collectionId": users_collection_id,
                "cascadeDelete": False,
                "maxSelect": 1,
            },
            {
                "name": "role_name",
                "type": "text",
                "required": False,
            },
            {
                "name": "company_name",
                "type": "text",
                "required": False,
            },
            {
                "name": "file",
                "type": "file",
                "required": False,
                "maxSelect": 1,
                "maxSize": 5242880,
                "mimeTypes": ["application/pdf", "text/plain"],
            },
            {
                "name": "original_text",
                "type": "text",
                "required": False,
            },
            {
                "name": "generated_questions",
                "type": "json",
                "required": False,
            },
            {
                "name": "created",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": False,
            },
            {
                "name": "updated",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": True,
            }
        ],
        "listRule": "user = @request.auth.id",
        "viewRule": "user = @request.auth.id",
        "createRule": "@request.auth.id != '' && user = @request.auth.id",
        "updateRule": "user = @request.auth.id",
        "deleteRule": "user = @request.auth.id",
    }
    
def get_scoring_results_schema(resume_collection_id: str, jd_collection_id: str, users_collection_id: str = "_pb_users_auth_") -> Dict[str, Any]:
    return {
        "name": "scoring_results",
        "type": "base",
        "fields": [
            {
                "name": "user",
                "type": "relation",
                "required": True,
                "collectionId": users_collection_id,
                "cascadeDelete": False,
                "maxSelect": 1,
            },
            {
                "name": "resume",
                "type": "relation",
                "required": True,
                "collectionId": resume_collection_id,
                "cascadeDelete": False,
                "maxSelect": 1,
            },
            {
                "name": "jd",
                "type": "relation",
                "required": True,
                "collectionId": jd_collection_id,
                "cascadeDelete": False,
                "maxSelect": 1,
            },
            {
                "name": "score",
                "type": "number",
                "required": False,
                "min": 0,
                "max": 10,
            },
            {
                "name": "analysis",
                "type": "json",
                "required": False,
            },
            {
                "name": "status",
                "type": "select",
                "required": True,
                "maxSelect": 1,
                "values": ["queued", "processing", "completed", "failed"],
            },
            {
                "name": "created",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": False,
            },
            {
                "name": "updated",
                "type": "autodate",
                "onCreate": True,
                "onUpdate": True,
            }
        ],
        "listRule": "user = @request.auth.id",
        "viewRule": "user = @request.auth.id",
        "createRule": "@request.auth.id != '' && user = @request.auth.id", 
        "updateRule": "", 
        "deleteRule": "user = @request.auth.id",
    }

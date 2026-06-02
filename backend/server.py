from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


class WaitlistCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr


class WaitlistEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    segment: str = "Local wealth / law office sandbox"
    access_tier: str = "Sandboxed early access"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Project Artemis API online"}


@api_router.post("/waitlist", response_model=WaitlistEntry, status_code=201)
async def create_waitlist_entry(input: WaitlistCreate):
    clean_email = input.email.lower().strip()
    clean_name = " ".join(input.name.strip().split())

    existing = await db.waitlist_entries.find_one({"email": clean_email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="This email is already on the Artemis sandbox list.")

    entry = WaitlistEntry(name=clean_name, email=clean_email)
    doc = entry.model_dump()
    await db.waitlist_entries.insert_one(doc)
    return entry


@api_router.get("/waitlist", response_model=List[WaitlistEntry])
async def get_waitlist_entries():
    entries = await db.waitlist_entries.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return entries

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
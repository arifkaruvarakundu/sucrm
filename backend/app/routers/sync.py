from fastapi import APIRouter, Depends
from app.models import WhatsAppTemplate
from app.schemas import WhatsAppTemplateBase
from sqlalchemy.orm import Session
from app.database import get_db
from typing import List
from dotenv import load_dotenv
import os
from datetime import datetime
import requests

load_dotenv()

ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WABA_ID = os.getenv("WABA_ID")

router = APIRouter()

@router.post("/sync-templates")
def sync_templates(db: Session = Depends(get_db)):
    url = f"https://graph.facebook.com/v20.0/{WABA_ID}/message_templates"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": response.json()}

    templates = response.json().get("data", [])

    for t in templates:
        body_component = next((c for c in t.get("components", []) if c["type"] == "BODY"), {})
        
        # UPSERT logic using SQLAlchemy ORM
        existing = db.query(WhatsAppTemplate).filter_by(template_name=t["name"]).first()
        if existing:
            existing.category = t["category"]
            existing.language = t["language"]
            existing.status = t["status"]
            existing.body = body_component.get("text")
            existing.updated_at = datetime.utcnow()
        else:
            new_template = WhatsAppTemplate(
                template_name=t["name"],
                category=t["category"],
                language=t["language"],
                status=t["status"],
                body=body_component.get("text"),
                updated_at=datetime.utcnow()
            )
            db.add(new_template)

    db.commit()

    return {"message": f"✅ Synced {len(templates)} templates"}

@router.get("/templates/", response_model=List[WhatsAppTemplateBase])
def get_templates(db: Session = Depends(get_db)):

    templates = db.query(WhatsAppTemplate).all()

    return templates
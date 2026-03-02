from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base
import crud,schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shortener")
templates = Jinja2Templates(directory="templates")

def record_click(db : Session, link_id:int, click_data:dict):

    try:
        crud.create_click(db, link_id, schemas.ClickBase(**click_data))
    finally:
        db.close()


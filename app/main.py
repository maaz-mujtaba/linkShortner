'''from fastapi import Depends, FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, engine
from models import Base, Link  # Import Link model
import crud
import schemas

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shortener")
templates = Jinja2Templates(directory="templates")

def record_click(link_id: int, click_data: dict):
    """Background task to record clicks"""
    db = SessionLocal()
    try:
        crud.create_click(db, link_id, schemas.ClickBase(**click_data))
    finally:
        db.close()

@app.post("/shorten", response_model=schemas.Link)
def create_short_link(link: schemas.LinkCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_link(db, link)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/{short_code}")
def redirect_to_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    link = crud.get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    click_data = schemas.ClickBase(
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer")
    )

    # Fix: Pass only the necessary data to background task
    background_tasks.add_task(record_click, link.id, click_data.dict())

    return RedirectResponse(url=link.original_url, status_code=302)

@app.get("/stats/{short_code}", response_model=schemas.LinkStats)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    link = crud.get_link_stats(db, short_code)  # This now uses short_code
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@app.get("/api/links", response_model=list[schemas.Link])
def list_links(db: Session = Depends(get_db)):
    # Fix: Query the Link model, not the schema
    return db.query(Link).all()

@app.get("/dashboard", response_class=HTMLResponse)  # Changed from "/" to "/dashboard"
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content="""
    <html>
        <body>
            <h1>Link Shortener API</h1>
            <p>Go to <a href="/dashboard">Dashboard</a> or <a href="/docs">API Documentation</a></p>
        </body>
    </html>
    """)

'''

from fastapi import Depends, FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, engine
from models import Base, Link
import crud
import schemas

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shortener")
templates = Jinja2Templates(directory="templates")


def record_click(link_id: int, click_data: dict):
    """Background task to record clicks"""
    db = SessionLocal()
    try:
        crud.create_click(db, link_id, schemas.ClickBase(**click_data))
    finally:
        db.close()


# -------------------------
# API ROUTES (STATIC FIRST)
# -------------------------

@app.post("/shorten", response_model=schemas.Link)
def create_short_link(link: schemas.LinkCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_link(db, link)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/stats/{short_code}", response_model=schemas.LinkStats)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    link = crud.get_link_stats(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@app.get("/api/links", response_model=list[schemas.Link])
def list_links(db: Session = Depends(get_db)):
    return db.query(Link).all()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content="""
    <html>
        <body>
            <h1>Link Shortener API</h1>
            <p>Go to <a href="/dashboard">Dashboard</a> or <a href="/docs">API Documentation</a></p>
        </body>
    </html>
    """)


# -------------------------
# DYNAMIC ROUTE (MUST BE LAST)
# -------------------------

@app.get("/{short_code}")
def redirect_to_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    link = crud.get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    click_data = schemas.ClickBase(
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer")
    )

    background_tasks.add_task(record_click, link.id, click_data.dict())

    return RedirectResponse(url=link.original_url, status_code=302)
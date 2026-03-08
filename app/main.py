'''from fastapi import Depends, FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, engine
from models import Base, Link
import crud
import schemas
from cache_utils import get_cached_link, invalidate_cache, cache
from redis_config import redis_client
import time

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
'''

from fastapi import Depends, FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, engine
from models import Base, Link
import crud
import schemas
from cache_utils import get_cached_link, invalidate_link_cache, cache
from redis_config import redis_client
import time

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shortener with Redis Cache")
templates = Jinja2Templates(directory="templates")

# Health check endpoint for Redis
@app.get("/health")
def health_check():
    """Check if Redis is connected"""
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "degraded", "redis": f"disconnected: {e}"}

def record_click(link_id: int, short_code: str, click_data: dict):
    """Background task to record clicks with cache update"""
    db = SessionLocal()
    try:
        # Record in database
        crud.create_click(db, link_id, schemas.ClickBase(**click_data))
        
        # Update cache
        cache.increment_clicks(short_code)
        
        # Get updated link and refresh cache
        link = crud.get_link_by_code(db, short_code)
        if link:
            from cache_utils import link_to_dict
            cache.set_link(short_code, link_to_dict(link))
    finally:
        db.close()

@app.post("/shorten", response_model=schemas.Link)
def create_short_link(link: schemas.LinkCreate, db: Session = Depends(get_db)):
    try:
        # Create link in database
        db_link = crud.create_link(db, link)
        
        # Cache the new link
        from cache_utils import link_to_dict
        cache.set_link(db_link.short_code, link_to_dict(db_link))
        
        return db_link
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/{short_code}")
def redirect_to_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Don't redirect special paths
    if short_code in ["dashboard", "api", "docs", "redoc", "openapi.json", "health"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Get link from cache or database
    link = get_cached_link(db, short_code)
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Track click asynchronously
    click_data = schemas.ClickBase(
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer")
    )
    
    background_tasks.add_task(record_click, link.id, short_code, click_data.dict())
    
    return RedirectResponse(url=link.original_url, status_code=302)

@app.get("/stats/{short_code}", response_model=schemas.LinkStats)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    # Get from cache first
    link = get_cached_link(db, short_code)
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Get full link with clicks from database
    full_link = crud.get_link_stats(db, short_code)
    return full_link

@app.get("/api/links", response_model=list[schemas.Link])
def list_links(db: Session = Depends(get_db)):
    # For listing all links, we still go to database
    # Could implement cache for this too if needed
    return db.query(Link).all()

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content="""
    <html>
        <body>
            <h1>Link Shortener API with Redis Cache</h1>
            <p>Go to <a href="/dashboard">Dashboard</a> or <a href="/docs">API Documentation</a></p>
            <p>Check <a href="/health">Health Status</a></p>
        </body>
    </html>
    """)

# Optional: Cache stats endpoint
@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    try:
        info = redis_client.info()
        return {
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "total_connections_received": info.get("total_connections_received"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "uptime_in_seconds": info.get("uptime_in_seconds")
        }
    except Exception as e:
        return {"error": str(e)}
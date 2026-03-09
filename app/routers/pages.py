from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

@router.get("/audit-logs", response_class=HTMLResponse)
async def audit_logs_page(request: Request):
    return templates.TemplateResponse("audit_logs.html", {"request": request})

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/sites/{site_id}", response_class=HTMLResponse)
async def view_site(request: Request, site_id: int):
    return templates.TemplateResponse("site.html", {"request": request, "site_id": site_id})

@router.get("/racks/{rack_id}", response_class=HTMLResponse)
async def view_rack(request: Request, rack_id: int):
    return templates.TemplateResponse("rack.html", {"request": request, "rack_id": rack_id})

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.controllers import create_user, get_user_by_username, verify_password
from sqlalchemy import select
from auth.models import User, UserProfile
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates/auth")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register_user(
    request: Request,
    name: str = Form(...),
    surname: str = Form(...),
    username: str = Form(...), 
    password: str = Form(...), 
    db: AsyncSession = Depends(get_db)
):
    existing_user = await get_user_by_username(db, username)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Bu istifadəçi adı qeydiyyatdan keçib!"
        })
    
    await create_user(db, name, surname, username, password)
    return RedirectResponse("/auth/login?msg=reg_success", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_user(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "İstifadəçi adı və ya şifrə yanlışdır!"
        })

    response = RedirectResponse(url="/auth/profile?msg=login_success", status_code=302)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response



@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login?msg=logout_success")
    response.delete_cookie("user_id")
    return response



@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login?msg=auth_required", status_code=302)

    stmt = select(User).options(selectinload(User.profile)).where(User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": user, 
        "profile": user.profile
    })

@router.post("/profile")
async def update_profile(
        request: Request,
        phone: str = Form(None),
        age: int = Form(None),
        country: str = Form(None),
        city: str = Form(None),
        address: str = Form(None),
        zip_code: str = Form(None),
        db: AsyncSession = Depends(get_db),
    ):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login", status_code=302)

    try:
        stmt = select(UserProfile).where(UserProfile.user_id == int(user_id))
        result = await db.execute(stmt)
        profile = result.scalar_one()
        
        profile.phone = phone
        profile.age = age
        profile.country = country
        profile.city = city
        profile.address = address
        profile.zip_code = zip_code
        
        await db.commit()
        return RedirectResponse("/auth/profile?msg=update_success", status_code=302)
    except Exception:
        return RedirectResponse("/auth/profile?msg=update_error", status_code=302)
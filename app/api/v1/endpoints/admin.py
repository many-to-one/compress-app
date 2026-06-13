from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from models.user import User
from crud.user import get_current_user, admin_required
from fastapi.responses import RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# LISTA UŻYTKOWNIKÓW
@router.get("/users")
async def admin_users(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()

    user = request.state.user

    if not user or not user.is_admin:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "users": users}
    )


# SZCZEGÓŁY UŻYTKOWNIKA
@router.get("/user/{user_id}")
async def admin_user_detail(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    return templates.TemplateResponse(
        "admin_user_detail.html",
        {"request": request, "user": user}
    )


# BLOKOWANIE UŻYTKOWNIKA
@router.get("/block/{user_id}")
async def admin_block_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    user.is_blocked = True
    user.blocked_ips = list(set(user.ips))

    db.add(user)
    await db.commit()

    return RedirectResponse(f"/admin/user/{user_id}", status_code=302)


# ODBLOKOWANIE UŻYTKOWNIKA
@router.get("/unblock/{user_id}")
async def admin_unblock_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    user.is_blocked = False

    db.add(user)
    await db.commit()

    return RedirectResponse(f"/admin/user/{user_id}", status_code=302)


# BLOKOWANIE IP
@router.get("/block_ip/{user_id}/{ip}")
async def admin_block_ip(user_id: int, ip: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()


    if ip not in user.blocked_ips:
        user.blocked_ips.append(ip)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "blocked_ips")

    db.add(user)
    await db.commit()

    print("============= user.blocked_ips =============", user.blocked_ips)

    return RedirectResponse(f"/admin/user/{user_id}", status_code=302)


# ODBLOKOWANIE IP
@router.get("/unblock_ip/{user_id}/{ip}")
async def admin_unblock_ip(user_id: int, ip: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if ip in user.blocked_ips:
        user.blocked_ips.remove(ip)

    db.add(user)
    await db.commit()

    return RedirectResponse(f"/admin/user/{user_id}", status_code=302)

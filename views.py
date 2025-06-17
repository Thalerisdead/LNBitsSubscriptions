from http import HTTPStatus

from fastapi import Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from lnbits.core.models import User
from lnbits.decorators import check_user_exists

from . import subscriptions_ext, subscriptions_renderer
from .crud import get_subscription_plan


templates = Jinja2Templates(directory="templates")


@subscriptions_ext.get("/")
async def index(request: Request, user: User = Depends(check_user_exists)):
    """Main subscriptions dashboard."""
    return subscriptions_renderer().TemplateResponse(
        "subscriptions/index.html", {"request": request, "user": user.dict()}
    )


@subscriptions_ext.get("/plans")
async def plans_page(request: Request, user: User = Depends(check_user_exists)):
    """Subscription plans management page."""
    return subscriptions_renderer().TemplateResponse(
        "subscriptions/plans.html", {"request": request, "user": user.dict()}
    )


@subscriptions_ext.get("/subscriptions")
async def subscriptions_page(request: Request, user: User = Depends(check_user_exists)):
    """Subscriptions management page."""
    return subscriptions_renderer().TemplateResponse(
        "subscriptions/subscriptions.html", {"request": request, "user": user.dict()}
    )


@subscriptions_ext.get("/subscribe/{plan_id}")
async def public_subscribe_page(request: Request, plan_id: str):
    """Public subscription page for customers."""
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Plan not found"
        )
    
    return subscriptions_renderer().TemplateResponse(
        "subscriptions/subscribe.html", 
        {
            "request": request, 
            "plan": plan.dict(),
            "plan_id": plan_id
        }
    ) 
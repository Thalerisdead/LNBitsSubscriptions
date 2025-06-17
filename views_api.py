import asyncio
import json
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import List, Optional
import ipaddress

from fastapi import Depends, HTTPException, Query, Request
from lnbits.core.crud import get_user, get_wallet
from lnbits.core.models import Payment, User, Wallet
from lnbits.core.services import create_invoice, pay_invoice
from lnbits.decorators import WalletTypeInfo, get_key_type, require_admin_key
from lnbits.helpers import template_renderer
from loguru import logger

# Simple rate limiting storage (in production, use Redis)
_rate_limit_storage = {}

def check_rate_limit(request: Request, max_requests: int = 5, window_minutes: int = 1) -> bool:
    """Simple rate limiting implementation."""
    client_ip = request.client.host if request.client else "unknown"
    current_time = datetime.now()
    window_key = f"{client_ip}:{current_time.strftime('%Y-%m-%d-%H-%M')}"
    
    # Clean old entries
    keys_to_remove = []
    for key in _rate_limit_storage:
        key_time = datetime.strptime(key.split(':', 1)[1], '%Y-%m-%d-%H-%M')
        if (current_time - key_time).total_seconds() > window_minutes * 60:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del _rate_limit_storage[key]
    
    # Check current rate
    current_count = _rate_limit_storage.get(window_key, 0)
    if current_count >= max_requests:
        return False
    
    _rate_limit_storage[window_key] = current_count + 1
    return True

async def validate_plan_id(plan_id: str) -> None:
    """Validate plan ID format to prevent injection attacks."""
    if not plan_id or len(plan_id) < 5 or len(plan_id) > 50:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid plan ID format")
    
    # Check if plan ID contains only allowed characters
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', plan_id):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Plan ID contains invalid characters")

from . import subscriptions_ext
from .crud import (
    create_subscription_plan,
    create_subscription,
    get_subscription_plan,
    get_subscription_plans,
    get_subscriptions,
    get_subscriptions_by_plan,
    update_subscription_plan,
    delete_subscription_plan,
    cancel_subscription,
    get_subscription,
    create_subscription_payment,
    get_subscription_payments,
    update_payment_status,
    get_due_subscriptions,
)
from .models import (
    CreateSubscriptionPlan,
    CreateSubscription,
    SubscriptionPlan,
    Subscription,
    SubscriptionPayment,
)


# Subscription Plans API
@subscriptions_ext.post("/api/v1/plans")
async def api_create_plan(
    data: CreateSubscriptionPlan, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    """Create a new subscription plan."""
    try:
        plan = await create_subscription_plan(wallet.wallet.id, data)
        return plan.dict()
    except Exception as e:
        logger.error(f"Error creating subscription plan: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not create subscription plan"
        )


@subscriptions_ext.get("/api/v1/plans")
async def api_get_plans(
    wallet: WalletTypeInfo = Depends(get_key_type)
) -> List[dict]:
    """Get all subscription plans for a wallet."""
    try:
        plans = await get_subscription_plans(wallet.wallet.id)
        return [plan.dict() for plan in plans]
    except Exception as e:
        logger.error(f"Error fetching subscription plans: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not fetch subscription plans"
        )


@subscriptions_ext.get("/api/v1/plans/{plan_id}")
async def api_get_plan(
    plan_id: str, wallet: WalletTypeInfo = Depends(get_key_type)
):
    """Get a specific subscription plan."""
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Plan not found"
        )
    
    if plan.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Access denied"
        )
    
    return plan.dict()


@subscriptions_ext.put("/api/v1/plans/{plan_id}")
async def api_update_plan(
    plan_id: str,
    data: CreateSubscriptionPlan,
    wallet: WalletTypeInfo = Depends(require_admin_key)
):
    """Update a subscription plan."""
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Plan not found"
        )
    
    if plan.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Access denied"
        )
    
    try:
        updated_plan = await update_subscription_plan(plan_id, data)
        return updated_plan.dict()
    except Exception as e:
        logger.error(f"Error updating subscription plan: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not update subscription plan"
        )


@subscriptions_ext.delete("/api/v1/plans/{plan_id}")
async def api_delete_plan(
    plan_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    """Delete a subscription plan."""
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Plan not found"
        )
    
    if plan.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Access denied"
        )
    
    # Check if there are active subscriptions
    subscriptions = await get_subscriptions_by_plan(plan_id)
    active_subs = [s for s in subscriptions if s.status in ["active", "trialing", "past_due"]]
    
    if active_subs:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Cannot delete plan with {len(active_subs)} active subscriptions"
        )
    
    try:
        await delete_subscription_plan(plan_id)
        return {"message": "Plan deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting subscription plan: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not delete subscription plan"
        )


# Subscriptions API
@subscriptions_ext.post("/api/v1/subscriptions")
async def api_create_subscription(
    data: CreateSubscription, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    """Create a new subscription."""
    try:
        subscription = await create_subscription(data.plan_id, wallet.wallet.id, data)
        return subscription.dict()
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not create subscription"
        )


@subscriptions_ext.get("/api/v1/subscriptions")
async def api_get_subscriptions(
    wallet: WalletTypeInfo = Depends(get_key_type)
) -> List[dict]:
    """Get all subscriptions for a wallet."""
    try:
        subscriptions = await get_subscriptions(wallet.wallet.id)
        return [sub.dict() for sub in subscriptions]
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not fetch subscriptions"
        )


@subscriptions_ext.get("/api/v1/subscriptions/{subscription_id}")
async def api_get_subscription(
    subscription_id: str, wallet: WalletTypeInfo = Depends(get_key_type)
):
    """Get a specific subscription."""
    subscription = await get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Subscription not found"
        )
    
    if subscription.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Access denied"
        )
    
    return subscription.dict()


@subscriptions_ext.post("/api/v1/subscriptions/{subscription_id}/cancel")
async def api_cancel_subscription(
    subscription_id: str,
    at_period_end: bool = Query(True, description="Cancel at the end of current period"),
    wallet: WalletTypeInfo = Depends(require_admin_key)
):
    """Cancel a subscription."""
    subscription = await get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Subscription not found"
        )
    
    if subscription.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Access denied"
        )
    
    try:
        updated_subscription = await cancel_subscription(subscription_id, at_period_end)
        return updated_subscription.dict()
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not cancel subscription"
        )


@subscriptions_ext.get("/api/v1/plans/{plan_id}/subscriptions")
async def api_get_plan_subscriptions(
    plan_id: str, wallet: WalletTypeInfo = Depends(get_key_type)
) -> List[dict]:
    """Get all subscriptions for a specific plan."""
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Plan not found"
        )
    
    if plan.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Access denied"
        )
    
    try:
        subscriptions = await get_subscriptions_by_plan(plan_id)
        return [sub.dict() for sub in subscriptions]
    except Exception as e:
        logger.error(f"Error fetching plan subscriptions: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not fetch plan subscriptions"
        )


# Payments API
@subscriptions_ext.get("/api/v1/subscriptions/{subscription_id}/payments")
async def api_get_subscription_payments(
    subscription_id: str, wallet: WalletTypeInfo = Depends(get_key_type)
) -> List[dict]:
    """Get all payments for a subscription."""
    subscription = await get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Subscription not found"
        )
    
    if subscription.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Access denied"
        )
    
    try:
        payments = await get_subscription_payments(subscription_id)
        return [payment.dict() for payment in payments]
    except Exception as e:
        logger.error(f"Error fetching subscription payments: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not fetch subscription payments"
        )


# Public API for subscription creation (without auth)
@subscriptions_ext.post("/api/v1/public/subscribe/{plan_id}")
async def api_public_subscribe(request: Request, plan_id: str, data: CreateSubscription):
    """Public endpoint for creating subscriptions."""
    # Rate limiting
    if not check_rate_limit(request, max_requests=5, window_minutes=1):
        raise HTTPException(
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Validate plan ID format
    await validate_plan_id(plan_id)
    
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Plan not found"
        )
    
    # Check if plan has max subscription limit
    if plan.max_subscriptions and plan.active_subscriptions >= plan.max_subscriptions:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Plan has reached maximum number of subscriptions"
        )
    
    try:
        subscription = await create_subscription(plan_id, plan.wallet, data)
        
        # Create initial payment if not in trial
        if plan.trial_days == 0:
            payment_request = await create_invoice(
                wallet_id=plan.wallet,
                amount=plan.amount,
                memo=f"Subscription payment for {plan.name}",
                extra={"tag": "subscriptions", "subscription_id": subscription.id}
            )
            
            await create_subscription_payment(
                subscription.id,
                payment_request.payment_hash,
                plan.amount,
                subscription.current_period_start,
                subscription.current_period_end
            )
            
            return {
                "subscription": subscription.dict(),
                "payment_request": payment_request.bolt11,
                "payment_hash": payment_request.payment_hash
            }
        
        return {
            "subscription": subscription.dict(),
            "trial_days": plan.trial_days,
            "message": f"Trial period of {plan.trial_days} days activated"
        }
        
    except Exception as e:
        logger.error(f"Error creating public subscription: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not create subscription"
        )


@subscriptions_ext.get("/api/v1/public/plans/{plan_id}")
async def api_public_get_plan(plan_id: str):
    """Public endpoint to get plan details."""
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Plan not found"
        )
    
    # Return only public information
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "amount": plan.amount,
        "interval": plan.interval,
        "trial_days": plan.trial_days,
        "available_slots": (
            plan.max_subscriptions - plan.active_subscriptions
            if plan.max_subscriptions else None
        )
    } 
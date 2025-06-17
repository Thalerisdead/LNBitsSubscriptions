import json
from datetime import datetime, timedelta
from typing import List, Optional

from lnbits.helpers import urlsafe_short_hash

from . import db
from .models import (
    CreateSubscriptionPlan,
    SubscriptionPlan,
    CreateSubscription,
    Subscription,
    SubscriptionPayment,
)


# Subscription Plans CRUD
async def create_subscription_plan(
    wallet_id: str, data: CreateSubscriptionPlan
) -> SubscriptionPlan:
    plan_id = urlsafe_short_hash()
    now = datetime.now()
    
    await db.execute(
        """
        INSERT INTO subscriptions.plans (id, wallet, name, description, amount, interval, 
                                       trial_days, max_subscriptions, webhook_url, 
                                       success_message, success_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan_id,
            wallet_id,
            data.name,
            data.description,
            data.amount,
            data.interval,
            data.trial_days or 0,
            data.max_subscriptions,
            data.webhook_url,
            data.success_message,
            data.success_url,
            now,
            now,
        ),
    )
    
    plan = await get_subscription_plan(plan_id)
    assert plan, "Newly created plan couldn't be retrieved"
    return plan


async def get_subscription_plan(plan_id: str) -> Optional[SubscriptionPlan]:
    row = await db.fetchone(
        "SELECT * FROM subscriptions.plans WHERE id = ?", (plan_id,)
    )
    return SubscriptionPlan.from_row(row) if row else None


async def get_subscription_plans(wallet_id: str) -> List[SubscriptionPlan]:
    rows = await db.fetchall(
        "SELECT * FROM subscriptions.plans WHERE wallet = ? ORDER BY created_at DESC",
        (wallet_id,),
    )
    return [SubscriptionPlan.from_row(row) for row in rows]


async def update_subscription_plan(
    plan_id: str, data: CreateSubscriptionPlan
) -> Optional[SubscriptionPlan]:
    await db.execute(
        """
        UPDATE subscriptions.plans SET 
        name = ?, description = ?, amount = ?, interval = ?, trial_days = ?,
        max_subscriptions = ?, webhook_url = ?, success_message = ?, success_url = ?,
        updated_at = ?
        WHERE id = ?
        """,
        (
            data.name,
            data.description,
            data.amount,
            data.interval,
            data.trial_days or 0,
            data.max_subscriptions,
            data.webhook_url,
            data.success_message,
            data.success_url,
            datetime.now(),
            plan_id,
        ),
    )
    return await get_subscription_plan(plan_id)


async def delete_subscription_plan(plan_id: str) -> None:
    await db.execute("DELETE FROM subscriptions.plans WHERE id = ?", (plan_id,))


# Subscriptions CRUD
async def create_subscription(
    plan_id: str, wallet_id: str, data: CreateSubscription
) -> Subscription:
    plan = await get_subscription_plan(plan_id)
    if not plan:
        raise ValueError("Plan not found")
    
    subscription_id = urlsafe_short_hash()
    now = datetime.now()
    
    # Calculate trial period and first payment date
    if plan.trial_days > 0:
        trial_end = now + timedelta(days=plan.trial_days)
        current_period_start = now
        current_period_end = trial_end
        next_payment_date = trial_end
        status = "trialing"
    else:
        trial_end = None
        current_period_start = now
        
        # Calculate period end based on interval
        if plan.interval == "daily":
            current_period_end = now + timedelta(days=1)
        elif plan.interval == "weekly":
            current_period_end = now + timedelta(weeks=1)
        elif plan.interval == "monthly":
            current_period_end = now + timedelta(days=30)
        elif plan.interval == "yearly":
            current_period_end = now + timedelta(days=365)
        else:
            raise ValueError("Invalid interval")
        
        next_payment_date = now
        status = "active"
    
    await db.execute(
        """
        INSERT INTO subscriptions.subscriptions 
        (id, plan_id, wallet, subscriber_email, subscriber_name, status,
         current_period_start, current_period_end, trial_end, cancel_at_period_end,
         metadata, next_payment_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subscription_id,
            plan_id,
            wallet_id,
            data.subscriber_email,
            data.subscriber_name,
            status,
            current_period_start,
            current_period_end,
            trial_end,
            False,
            json.dumps(data.metadata) if data.metadata else None,
            next_payment_date,
            now,
            now,
        ),
    )
    
    # Update plan's active subscription count
    await db.execute(
        """
        UPDATE subscriptions.plans 
        SET active_subscriptions = active_subscriptions + 1 
        WHERE id = ?
        """,
        (plan_id,),
    )
    
    subscription = await get_subscription(subscription_id)
    assert subscription, "Newly created subscription couldn't be retrieved"
    return subscription


async def get_subscription(subscription_id: str) -> Optional[Subscription]:
    row = await db.fetchone(
        "SELECT * FROM subscriptions.subscriptions WHERE id = ?", (subscription_id,)
    )
    return Subscription.from_row(row) if row else None


async def get_subscriptions(wallet_id: str) -> List[Subscription]:
    rows = await db.fetchall(
        "SELECT * FROM subscriptions.subscriptions WHERE wallet = ? ORDER BY created_at DESC",
        (wallet_id,),
    )
    return [Subscription.from_row(row) for row in rows]


async def get_subscriptions_by_plan(plan_id: str) -> List[Subscription]:
    rows = await db.fetchall(
        "SELECT * FROM subscriptions.subscriptions WHERE plan_id = ? ORDER BY created_at DESC",
        (plan_id,),
    )
    return [Subscription.from_row(row) for row in rows]


async def update_subscription_status(
    subscription_id: str, status: str, canceled_at: Optional[datetime] = None
) -> Optional[Subscription]:
    await db.execute(
        """
        UPDATE subscriptions.subscriptions 
        SET status = ?, canceled_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, canceled_at, datetime.now(), subscription_id),
    )
    return await get_subscription(subscription_id)


async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> Optional[Subscription]:
    if at_period_end:
        await db.execute(
            """
            UPDATE subscriptions.subscriptions 
            SET cancel_at_period_end = ?, updated_at = ?
            WHERE id = ?
            """,
            (True, datetime.now(), subscription_id),
        )
    else:
        await db.execute(
            """
            UPDATE subscriptions.subscriptions 
            SET status = ?, canceled_at = ?, updated_at = ?
            WHERE id = ?
            """,
            ("canceled", datetime.now(), datetime.now(), subscription_id),
        )
    
    return await get_subscription(subscription_id)


# Subscription Payments CRUD
async def create_subscription_payment(
    subscription_id: str, payment_hash: str, amount: int, period_start: datetime, period_end: datetime
) -> SubscriptionPayment:
    payment_id = urlsafe_short_hash()
    now = datetime.now()
    
    await db.execute(
        """
        INSERT INTO subscriptions.payments 
        (id, subscription_id, payment_hash, amount, status, period_start, period_end, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (payment_id, subscription_id, payment_hash, amount, "pending", period_start, period_end, now),
    )
    
    payment = await get_subscription_payment(payment_id)
    assert payment, "Newly created payment couldn't be retrieved"
    return payment


async def get_subscription_payment(payment_id: str) -> Optional[SubscriptionPayment]:
    row = await db.fetchone(
        "SELECT * FROM subscriptions.payments WHERE id = ?", (payment_id,)
    )
    return SubscriptionPayment.from_row(row) if row else None


async def get_subscription_payments(subscription_id: str) -> List[SubscriptionPayment]:
    rows = await db.fetchall(
        "SELECT * FROM subscriptions.payments WHERE subscription_id = ? ORDER BY created_at DESC",
        (subscription_id,),
    )
    return [SubscriptionPayment.from_row(row) for row in rows]


async def update_payment_status(
    payment_id: str, status: str, failure_reason: Optional[str] = None
) -> Optional[SubscriptionPayment]:
    payment_date = datetime.now() if status == "paid" else None
    
    await db.execute(
        """
        UPDATE subscriptions.payments 
        SET status = ?, payment_date = ?, failure_reason = ?
        WHERE id = ?
        """,
        (status, payment_date, failure_reason, payment_id),
    )
    return await get_subscription_payment(payment_id)


async def get_due_subscriptions() -> List[Subscription]:
    """Get all subscriptions that are due for payment."""
    now = datetime.now()
    rows = await db.fetchall(
        """
        SELECT * FROM subscriptions.subscriptions 
        WHERE status IN ('active', 'past_due') 
        AND next_payment_date <= ?
        AND (canceled_at IS NULL OR canceled_at > ?)
        """,
        (now, now),
    )
    return [Subscription.from_row(row) for row in rows] 
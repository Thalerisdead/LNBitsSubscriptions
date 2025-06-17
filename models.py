import json
from datetime import datetime, timedelta
from typing import List, Optional, Literal
from urllib.parse import urlparse

from lnbits.helpers import urlsafe_short_hash
from pydantic import BaseModel, Field, validator, HttpUrl


class CreateSubscriptionPlan(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Plan name")
    description: Optional[str] = Field(None, max_length=500, description="Plan description")
    amount: int = Field(..., gt=0, le=21000000 * 100000000, description="Amount in satoshis")
    interval: Literal["daily", "weekly", "monthly", "yearly"] = Field(..., description="Billing interval")
    trial_days: Optional[int] = Field(0, ge=0, le=365, description="Free trial days")
    max_subscriptions: Optional[int] = Field(None, gt=0, le=1000000, description="Maximum subscriptions")
    webhook_url: Optional[str] = Field(None, max_length=500, description="Webhook URL")
    success_message: Optional[str] = Field(None, max_length=200, description="Success message")
    success_url: Optional[str] = Field(None, max_length=500, description="Success redirect URL")
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if v:
            try:
                parsed = urlparse(v)
                if not parsed.scheme or parsed.scheme not in ['http', 'https']:
                    raise ValueError('Webhook URL must use http or https')
                if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0'] or parsed.hostname.startswith('192.168.') or parsed.hostname.startswith('10.') or parsed.hostname.startswith('172.'):
                    raise ValueError('Webhook URL cannot point to private networks')
            except Exception:
                raise ValueError('Invalid webhook URL format')
        return v
    
    @validator('success_url')
    def validate_success_url(cls, v):
        if v:
            try:
                parsed = urlparse(v)
                if not parsed.scheme or parsed.scheme not in ['http', 'https']:
                    raise ValueError('Success URL must use http or https')
            except Exception:
                raise ValueError('Invalid success URL format')
        return v


class SubscriptionPlan(BaseModel):
    id: str
    wallet: str
    name: str
    description: Optional[str]
    amount: int
    interval: str
    trial_days: int
    max_subscriptions: Optional[int]
    active_subscriptions: int = 0
    webhook_url: Optional[str]
    success_message: Optional[str]
    success_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))


class CreateSubscription(BaseModel):
    plan_id: str = Field(..., min_length=1, max_length=50, description="Plan ID")
    subscriber_email: Optional[str] = Field(None, max_length=255, description="Subscriber email")
    subscriber_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Subscriber name")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator('subscriber_email')
    def validate_email(cls, v):
        if v:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v:
            # Limit metadata size and validate structure
            if len(str(v)) > 1000:
                raise ValueError('Metadata too large (max 1000 characters)')
            # Ensure it's a simple dict with string keys and values
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            for key, value in v.items():
                if not isinstance(key, str) or len(key) > 50:
                    raise ValueError('Metadata keys must be strings with max 50 characters')
                if not isinstance(value, (str, int, float, bool)) or (isinstance(value, str) and len(value) > 200):
                    raise ValueError('Metadata values must be simple types with max 200 characters for strings')
        return v


class Subscription(BaseModel):
    id: str
    plan_id: str
    wallet: str
    subscriber_email: Optional[str]
    subscriber_name: Optional[str]
    status: str  # "active", "past_due", "canceled", "trialing"
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime]
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    # Payment tracking
    last_payment_id: Optional[str]
    last_payment_date: Optional[datetime]
    failed_payment_count: int = 0
    next_payment_date: datetime

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        if data.get("metadata"):
            data["metadata"] = json.loads(data["metadata"])
        return cls(**data)


class SubscriptionPayment(BaseModel):
    id: str
    subscription_id: str
    payment_hash: str
    amount: int
    status: str  # "pending", "paid", "failed"
    period_start: datetime
    period_end: datetime
    payment_date: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row)) 
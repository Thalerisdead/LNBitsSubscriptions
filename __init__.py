import asyncio
from fastapi import APIRouter
from lnbits.db import Database
from lnbits.helpers import template_renderer

db = Database("ext_subscriptions")

subscriptions_ext: APIRouter = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

from .views import *  # noqa
from .views_api import *  # noqa

def subscriptions_renderer():
    return template_renderer(["subscriptions/templates"]) 
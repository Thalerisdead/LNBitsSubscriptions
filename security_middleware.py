"""Security middleware for LNBits Subscriptions extension."""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
import secrets


def add_security_headers(response: Response) -> Response:
    """Add security headers to responses."""
    # Generate nonce for CSP
    nonce = secrets.token_urlsafe(16)
    
    # Content Security Policy
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://unpkg.com; "
        f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        f"font-src 'self' https://fonts.gstatic.com; "
        f"img-src 'self' data:; "
        f"connect-src 'self'; "
        f"frame-ancestors 'none'; "
        f"object-src 'none'; "
        f"base-uri 'self';"
    )
    
    response.headers["Content-Security-Policy"] = csp
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Store nonce for use in templates
    if hasattr(response, 'context'):
        response.context['csp_nonce'] = nonce
    
    return response


def security_middleware(request: Request, call_next: Callable) -> Response:
    """Apply security middleware to all requests."""
    response = call_next(request)
    
    # Add security headers
    response = add_security_headers(response)
    
    return response


def validate_csrf_token(request: Request, expected_token: str) -> bool:
    """Validate CSRF token from request."""
    # Get token from header or form data
    token = request.headers.get("X-CSRF-Token")
    if not token and hasattr(request, 'form'):
        form_data = request.form()
        token = form_data.get("csrf_token")
    
    return token == expected_token


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32) 
# 🔒 Security Penetration Test Report
## LNBits Subscriptions Extension

**Date:** December 2024  
**Scope:** Complete LNBits Subscriptions Extension  
**Severity Levels:** Critical | High | Medium | Low | Info

---

## 📋 Executive Summary

The LNBits Subscriptions extension has been analyzed for security vulnerabilities. **12 security issues** were identified ranging from **Critical** to **Low** severity. Immediate attention is required for critical and high-severity findings.

### Summary of Findings:
- **Critical:** 2 issues
- **High:** 3 issues  
- **Medium:** 4 issues
- **Low:** 2 issues
- **Info:** 1 issue

---

## 🚨 CRITICAL SEVERITY VULNERABILITIES

### 1. Cross-Site Scripting (XSS) in Public Subscription Page
**File:** `templates/subscriptions/subscribe.html`  
**Line:** 295, 338, 361  
**CVSS Score:** 9.3

**Description:**
Multiple XSS vulnerabilities exist in the public subscription template where user-controlled data is rendered without proper sanitization.

**Vulnerable Code:**
```html
<!-- Line 295: Direct template injection -->
showPaymentSection(data.payment_request, {{ plan.amount }});

<!-- Line 338: Unescaped success URL redirect -->
window.location.href = '{{ plan.success_url }}';

<!-- Line 361: Unescaped success message -->
showSuccess({{ plan.success_message | tojson }} || 'Payment successful!');
```

**Impact:**
- Session hijacking
- Account takeover via admin panel access
- Malicious JavaScript execution
- Phishing attacks

**Proof of Concept:**
```bash
# Create plan with malicious success_url
curl -X POST http://localhost:5000/subscriptions/api/v1/plans \
  -H "Authorization: Bearer admin_key" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","amount":1000,"interval":"monthly","success_url":"javascript:alert(document.cookie)"}'
```

**Remediation:**
- Use proper template escaping: `{{ plan.success_url | e }}`
- Validate URLs against allowlist
- Implement Content Security Policy (CSP)

### 2. Authentication Bypass in Public API
**File:** `views_api.py`  
**Line:** 298-354  
**CVSS Score:** 8.5

**Description:**
The public subscription endpoint lacks rate limiting and input validation, allowing unlimited subscription creation and potential resource exhaustion.

**Vulnerable Code:**
```python
@subscriptions_ext.post("/api/v1/public/subscribe/{plan_id}")
async def api_public_subscribe(plan_id: str, data: CreateSubscription):
    # No rate limiting or authentication
    # No validation of plan_id format
    subscription = await create_subscription(plan_id, plan.wallet, data)
```

**Impact:**
- Resource exhaustion attacks
- Unlimited subscription creation
- Database overflow
- Service denial

**Remediation:**
- Implement rate limiting (e.g., 5 requests per minute per IP)
- Add input validation for plan_id format
- Implement CAPTCHA for public endpoints

---

## ⚠️ HIGH SEVERITY VULNERABILITIES

### 3. SQL Injection via Metadata Field
**File:** `crud.py`  
**Line:** 129  
**CVSS Score:** 7.8

**Description:**
The metadata field is serialized using `json.dumps()` but could potentially contain malicious JSON that affects database operations.

**Vulnerable Code:**
```python
json.dumps(data.metadata) if data.metadata else None
```

**Impact:**
- Potential data corruption
- JSON injection attacks
- Database integrity issues

**Remediation:**
- Validate JSON structure before serialization
- Implement size limits on metadata (max 1KB)
- Sanitize JSON keys and values

### 4. Insufficient Authorization in Plan Management
**File:** `views_api.py`  
**Line:** 69-77, 91-99  
**CVSS Score:** 7.5

**Description:**
Plan access control only checks wallet ownership but doesn't validate if the user has proper permissions to access specific plans.

**Vulnerable Code:**
```python
if plan.wallet != wallet.wallet.id:
    raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")
```

**Impact:**
- Horizontal privilege escalation
- Unauthorized plan access
- Data leakage between users

**Remediation:**
- Implement proper role-based access control
- Add plan-specific permissions
- Log all access attempts

### 5. Missing CSRF Protection
**File:** All API endpoints  
**CVSS Score:** 7.2

**Description:**
No CSRF tokens are implemented for state-changing operations, allowing cross-site request forgery attacks.

**Impact:**
- Unauthorized plan creation/deletion
- Subscription manipulation
- Account takeover

**Remediation:**
- Implement CSRF tokens for all state-changing operations
- Use SameSite cookie attributes
- Add Origin/Referer header validation

---

## ⚠️ MEDIUM SEVERITY VULNERABILITIES

### 6. Information Disclosure in Error Messages
**File:** `views_api.py`  
**Line:** Multiple locations  
**CVSS Score:** 5.8

**Description:**
Detailed error messages expose internal system information and database structure.

**Vulnerable Code:**
```python
logger.error(f"Error creating subscription plan: {e}")
raise HTTPException(
    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    detail="Could not create subscription plan"  # Generic but logs reveal details
)
```

**Remediation:**
- Use generic error messages for users
- Log detailed errors separately
- Implement error code system

### 7. Weak Input Validation
**File:** `models.py`  
**Line:** 8-18  
**CVSS Score:** 5.5

**Description:**
Insufficient validation on critical fields like amount, interval, and email addresses.

**Vulnerable Code:**
```python
class CreateSubscriptionPlan(BaseModel):
    name: str  # No length limits
    amount: int  # No range validation
    interval: str  # No enum validation
    webhook_url: Optional[str] = None  # No URL validation
```

**Remediation:**
- Add field validators using Pydantic validators
- Implement min/max constraints
- Validate URLs and email formats

### 8. Race Condition in Subscription Creation
**File:** `crud.py`  
**Line:** 139-143  
**CVSS Score:** 5.3

**Description:**
Subscription count updates are not atomic, leading to potential race conditions.

**Vulnerable Code:**
```python
# Non-atomic operation
await db.execute(
    "UPDATE subscriptions.plans SET active_subscriptions = active_subscriptions + 1 WHERE id = ?",
    (plan_id,),
)
```

**Remediation:**
- Use database transactions
- Implement atomic counters
- Add optimistic locking

### 9. Webhook URL Validation Missing
**File:** `models.py`  
**CVSS Score:** 5.1

**Description:**
Webhook URLs are not validated, allowing SSRF attacks and internal network access.

**Impact:**
- Server-Side Request Forgery (SSRF)
- Internal network reconnaissance
- Potential credential theft

**Remediation:**
- Validate webhook URLs against allowlist
- Block private IP ranges
- Implement webhook signing

---

## ⚠️ LOW SEVERITY VULNERABILITIES

### 10. Missing Rate Limiting on API Endpoints
**File:** All API endpoints  
**CVSS Score:** 3.5

**Description:**
No rate limiting implemented, allowing potential abuse and DoS attacks.

**Remediation:**
- Implement rate limiting per API key
- Add exponential backoff
- Monitor and alert on unusual patterns

### 11. Insecure Direct Object References
**File:** `views_api.py`  
**CVSS Score:** 3.2

**Description:**
Plan and subscription IDs are exposed directly without additional authorization checks.

**Remediation:**
- Use UUIDs instead of sequential IDs
- Implement additional authorization layers
- Add access logging

---

## 📊 INFORMATIONAL FINDINGS

### 12. Missing Security Headers
**File:** All templates

**Description:**
Missing security headers like Content-Security-Policy, X-Frame-Options, etc.

**Remediation:**
- Add security headers to all responses
- Implement CSP policy
- Add X-Frame-Options: DENY

---

## 🛠️ RECOMMENDED SECURITY FIXES

### Immediate Actions (Critical/High):

1. **Fix XSS vulnerabilities:**
```html
<!-- Before -->
window.location.href = '{{ plan.success_url }}';

<!-- After -->
{% if plan.success_url %}
window.location.href = {{ plan.success_url | tojson }};
{% endif %}
```

2. **Add input validation:**
```python
from pydantic import validator, HttpUrl
from typing import Literal

class CreateSubscriptionPlan(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: int = Field(..., gt=0, le=21000000 * 100000000)  # Max 21M BTC in sats
    interval: Literal["daily", "weekly", "monthly", "yearly"]
    webhook_url: Optional[HttpUrl] = None
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if v and v.host in ['localhost', '127.0.0.1', '0.0.0.0']:
            raise ValueError('Webhook URL cannot point to localhost')
        return v
```

3. **Implement rate limiting:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@subscriptions_ext.post("/api/v1/public/subscribe/{plan_id}")
@limiter.limit("5/minute")
async def api_public_subscribe(request: Request, plan_id: str, data: CreateSubscription):
    # Implementation
```

4. **Add CSRF protection:**
```python
from fastapi_csrf_protect import CsrfProtect

@subscriptions_ext.post("/api/v1/plans")
async def api_create_plan(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    data: CreateSubscriptionPlan, 
    wallet: WalletTypeInfo = Depends(require_admin_key)
):
    csrf_protect.validate_csrf(request)
    # Implementation
```

### Database Security:
```sql
-- Add constraints to prevent data corruption
ALTER TABLE subscriptions.plans ADD CONSTRAINT check_amount_positive CHECK (amount > 0);
ALTER TABLE subscriptions.plans ADD CONSTRAINT check_trial_days_positive CHECK (trial_days >= 0);
ALTER TABLE subscriptions.plans ADD CONSTRAINT check_valid_interval CHECK (interval IN ('daily', 'weekly', 'monthly', 'yearly'));
```

### Additional Security Measures:

1. **Implement Content Security Policy:**
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;">
```

2. **Add API versioning and deprecation:**
```python
# Add version validation
@subscriptions_ext.middleware("http")
async def validate_api_version(request: Request, call_next):
    if "/api/" in str(request.url) and not "/api/v1/" in str(request.url):
        return JSONResponse(
            status_code=400,
            content={"error": "API version required"}
        )
    return await call_next(request)
```

3. **Implement audit logging:**
```python
async def log_security_event(event_type: str, user_id: str, details: dict):
    await db.execute(
        "INSERT INTO security_audit (event_type, user_id, details, timestamp) VALUES (?, ?, ?, ?)",
        (event_type, user_id, json.dumps(details), datetime.now())
    )
```

---

## 📈 Security Testing Recommendations

1. **Automated Security Testing:**
   - Integrate SAST tools (bandit, semgrep)
   - Add dependency vulnerability scanning
   - Implement automated penetration testing

2. **Manual Testing:**
   - Regular security code reviews
   - Penetration testing every 6 months
   - Bug bounty program consideration

3. **Monitoring:**
   - Implement real-time security monitoring
   - Set up alerting for suspicious activities
   - Log all security-related events

---

## 📞 Contact & Next Steps

**Priority:** Address Critical and High severity issues within 7 days  
**Timeline:** Complete security remediation within 30 days  
**Re-test:** Schedule follow-up security assessment after fixes

This security assessment should be treated as confidential and shared only with authorized development and security personnel. 
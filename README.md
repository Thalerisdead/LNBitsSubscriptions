# LNBits Subscriptions Extension

A comprehensive Bitcoin payment subscription management extension for LNBits that allows you to create and manage recurring Bitcoin payments for your products and services.

## Features

### 🔄 Flexible Billing Intervals
- **Daily**: Perfect for premium content or services
- **Weekly**: Great for newsletters or weekly services  
- **Monthly**: Standard subscription model
- **Yearly**: Annual plans with potential discounts

### 🎁 Trial Periods
- Offer free trials from 1 day to any duration
- Automatically converts to paid subscription after trial
- Increases customer conversion rates

### 👥 Subscription Management
- Track all active, past due, and canceled subscriptions
- View subscriber information and payment history
- Easy cancellation (immediate or at period end)
- Automatic renewal handling

### 💰 Payment Processing
- Native Bitcoin Lightning payments
- QR codes for easy mobile payments
- Real-time payment verification
- Automatic invoice generation

### 🔧 Advanced Features
- **Webhook Support**: Get notified of subscription events
- **Success Redirects**: Redirect customers after successful subscription
- **Custom Messages**: Personalize success messages
- **Subscription Limits**: Control maximum number of subscribers
- **Public Subscription Pages**: Beautiful customer-facing subscription forms

## Installation

1. **Enable Admin UI** in your LNBits instance by setting `LNBITS_ADMIN_UI=true` in your `.env` file
2. **Access Admin Panel** using your superuser URL
3. **Install Extension** by uploading this extension or adding it to your extensions directory
4. **Activate Extension** in the Admin UI

## Quick Start

### 1. Create Your First Subscription Plan

```python
# Example plan configuration
{
  "name": "Premium Monthly",
  "description": "Access to all premium features",
  "amount": 50000,  # 50,000 satoshis
  "interval": "monthly",
  "trial_days": 7,
  "max_subscriptions": 100
}
```

### 2. Share Subscription Link

Each plan gets a unique public URL:
```
https://your-lnbits.com/subscriptions/subscribe/{plan_id}
```

### 3. Manage Subscriptions

Monitor your subscriptions through the dashboard:
- View revenue analytics
- Track active subscribers
- Manage customer subscriptions
- Monitor payment history

## API Reference

### Subscription Plans

#### Create Plan
```http
POST /subscriptions/api/v1/plans
Authorization: Bearer {admin_key}
Content-Type: application/json

{
  "name": "Plan Name",
  "description": "Plan description",
  "amount": 50000,
  "interval": "monthly",
  "trial_days": 7,
  "max_subscriptions": 100,
  "webhook_url": "https://your-site.com/webhook",
  "success_message": "Welcome to our service!",
  "success_url": "https://your-site.com/welcome"
}
```

#### Get Plans
```http
GET /subscriptions/api/v1/plans
Authorization: Bearer {admin_key}
```

#### Update Plan
```http
PUT /subscriptions/api/v1/plans/{plan_id}
Authorization: Bearer {admin_key}
Content-Type: application/json
```

#### Delete Plan
```http
DELETE /subscriptions/api/v1/plans/{plan_id}
Authorization: Bearer {admin_key}
```

### Subscriptions

#### Get Subscriptions
```http
GET /subscriptions/api/v1/subscriptions
Authorization: Bearer {admin_key}
```

#### Cancel Subscription
```http
POST /subscriptions/api/v1/subscriptions/{subscription_id}/cancel?at_period_end=true
Authorization: Bearer {admin_key}
```

### Public Endpoints

#### Subscribe to Plan
```http
POST /subscriptions/api/v1/public/subscribe/{plan_id}
Content-Type: application/json

{
  "subscriber_email": "customer@example.com",
  "subscriber_name": "Customer Name"
}
```

#### Get Plan Details
```http
GET /subscriptions/api/v1/public/plans/{plan_id}
```

## Webhook Events

Configure webhook URLs to receive subscription events:

### Event Types
- `subscription.created` - New subscription created
- `subscription.trial_ended` - Trial period ended
- `subscription.payment_succeeded` - Payment successful
- `subscription.payment_failed` - Payment failed
- `subscription.canceled` - Subscription canceled

### Webhook Payload
```json
{
  "event": "subscription.payment_succeeded",
  "subscription": {
    "id": "sub_123",
    "plan_id": "plan_456",
    "status": "active",
    "subscriber_email": "customer@example.com",
    "amount": 50000,
    "interval": "monthly"
  },
  "payment": {
    "id": "pay_789",
    "amount": 50000,
    "payment_hash": "hash123"
  }
}
```

## Use Cases

### 🎯 SaaS Products
Create monthly/yearly subscription plans for your software service with trial periods to increase conversions.

### 📰 Content Subscriptions
Offer premium content access with daily, weekly, or monthly billing cycles.

### 🎮 Gaming Services
Provide VIP access or premium features with flexible subscription options.

### 🏋️ Fitness & Coaching
Monthly coaching programs or fitness app subscriptions with trial periods.

### 🎵 Media & Entertainment
Music, video, or podcast premium subscriptions with various billing intervals.

## Database Schema

### Plans Table
- `id` - Unique plan identifier
- `wallet` - Associated LNBits wallet
- `name` - Plan name
- `description` - Plan description
- `amount` - Price in satoshis
- `interval` - Billing interval (daily/weekly/monthly/yearly)
- `trial_days` - Free trial period
- `max_subscriptions` - Subscription limit
- `active_subscriptions` - Current active count
- `webhook_url` - Event notification URL
- `success_message` - Custom success message
- `success_url` - Post-subscription redirect

### Subscriptions Table
- `id` - Unique subscription identifier
- `plan_id` - Associated plan
- `wallet` - Wallet receiving payments
- `subscriber_email` - Customer email
- `subscriber_name` - Customer name
- `status` - Subscription status
- `current_period_start` - Billing period start
- `current_period_end` - Billing period end
- `trial_end` - Trial end date
- `next_payment_date` - Next payment due
- `metadata` - Additional data

### Payments Table
- `id` - Unique payment identifier
- `subscription_id` - Associated subscription
- `payment_hash` - Lightning payment hash
- `amount` - Payment amount
- `status` - Payment status
- `period_start` - Service period start
- `period_end` - Service period end

## Development

### Local Development
1. Clone LNBits repository
2. Add this extension to the extensions directory
3. Enable the extension in settings
4. Start LNBits development server

### Testing
```bash
# Run tests
python -m pytest tests/

# Test webhook endpoints
curl -X POST http://localhost:5000/subscriptions/api/v1/plans \
  -H "Authorization: Bearer your_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Plan","amount":1000,"interval":"monthly"}'
```

## Support

For issues, feature requests, or contributions:
- GitHub: [LNBits Repository](https://github.com/lnbits/lnbits)
- Telegram: [LNBits Community](https://t.me/lnbits)
- Documentation: [LNBits Wiki](https://github.com/lnbits/lnbits/wiki)

## License

This extension is part of LNBits and follows the same license terms.

---

**Built with ⚡ Lightning and 🧡 Bitcoin** 
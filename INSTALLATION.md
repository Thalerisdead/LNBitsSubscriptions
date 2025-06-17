# LNBits Subscriptions Extension - Installation Guide

## 📦 Installation Methods

### Method 1: Install via LNBits Extension Manager (Recommended)

1. **Access LNBits Admin UI**:
   - Go to your LNBits instance as a Super User
   - Navigate to **Settings** → **Extension Sources**

2. **Add Extension Source**:
   - Click **"Add"**
   - Paste this URL: `https://raw.githubusercontent.com/Thalerisdead/LNBitsSubscriptions/main/manifest.json`
   - Click **"Save"**

3. **Install Extension**:
   - Go to **Extensions** section
   - Find "Subscriptions" in the available extensions
   - Click **"Enable"** to install and activate

### Method 2: Manual Installation (Development)

1. **Clone LNBits Repository**:
   ```bash
   git clone https://github.com/lnbits/lnbits.git
   cd lnbits
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   npm i
   ```

3. **Add Subscriptions Extension**:
   ```bash
   cd lnbits/extensions/
   git clone https://github.com/Thalerisdead/LNBitsSubscriptions.git subscriptions
   cd subscriptions
   ```

4. **Start LNBits**:
   ```bash
   cd ../../..
   python -m lnbits
   ```

5. **Enable Extension**:
   - Open `http://localhost:5000`
   - Go to **Settings** → **Extensions**
   - Enable "Subscriptions"

### Method 3: Docker Installation

1. **Using Docker Compose**:
   ```yaml
   version: '3.8'
   services:
     lnbits:
       image: lnbits/lnbits:latest
       environment:
         - LNBITS_EXTENSIONS_MANIFESTS=https://raw.githubusercontent.com/Thalerisdead/LNBitsSubscriptions/main/manifest.json
       ports:
         - "5000:5000"
   ```

2. **Start Container**:
   ```bash
   docker-compose up -d
   ```

## 🔧 Configuration

### Environment Variables

Add these to your LNBits `.env` file if needed:

```bash
# Extension manifests (include our extension)
LNBITS_EXTENSIONS_MANIFESTS=https://raw.githubusercontent.com/Thalerisdead/LNBitsSubscriptions/main/manifest.json

# Security settings (recommended)
LNBITS_EXTENSIONS_RATE_LIMIT=100  # requests per minute
LNBITS_EXTENSIONS_REQUIRE_AUTH=true
```

### Database

The extension will automatically create the required database tables on first startup:
- `subscriptions_plans` - Subscription plans
- `subscriptions_subscriptions` - Active subscriptions
- `subscriptions_payments` - Payment history

## 🚀 Quick Start

### 1. Create Your First Subscription Plan

```bash
curl -X POST http://localhost:5000/subscriptions/api/v1/plans \
  -H "Authorization: Bearer YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Plan",
    "description": "Monthly premium subscription",
    "amount": 50000,
    "interval": "monthly",
    "trial_days": 7,
    "webhook_url": "https://your-site.com/webhook"
  }'
```

### 2. Get Plan Details

```bash
curl -X GET http://localhost:5000/subscriptions/api/v1/plans \
  -H "Authorization: Bearer YOUR_ADMIN_KEY"
```

### 3. Create Public Subscription Link

```bash
# Use the plan_id from step 1
curl -X POST http://localhost:5000/subscriptions/api/v1/public/subscribe/PLAN_ID \
  -H "Content-Type: application/json" \
  -d '{
    "subscriber_email": "customer@example.com",
    "subscriber_name": "Customer Name"
  }'
```

## 🔐 Security Testing

Run the included security test suite:

```bash
# Install test dependencies
pip install aiohttp

# Run security tests
python security_test.py
```

## 📊 Monitoring

### Check Extension Status

```bash
curl -X GET http://localhost:5000/api/v1/health
```

### View Extension Logs

```bash
# For development
tail -f lnbits.log

# For Docker
docker logs -f lnbits_container
```

## 🐛 Troubleshooting

### Common Issues

1. **Extension Not Showing**:
   - Verify manifest URL is accessible
   - Check LNBits logs for errors
   - Restart LNBits service

2. **Database Errors**:
   - Check database permissions
   - Verify migration ran successfully
   - Look for conflicts with existing tables

3. **API Authentication Errors**:
   - Verify admin key is correct
   - Check key permissions in LNBits
   - Ensure extension is enabled

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export DEBUG=1

# Start LNBits
python -m lnbits
```

### Reset Extension

To completely reset the extension:

```bash
# Stop LNBits
# Delete extension tables from database
# Restart LNBits
```

## 🔄 Updates

### Automatic Updates

If installed via Extension Manager, updates will be available through the LNBits UI.

### Manual Updates

```bash
cd lnbits/extensions/subscriptions
git pull origin main
# Restart LNBits
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Thalerisdead/LNBitsSubscriptions/issues)
- **LNBits Community**: [Telegram Group](https://t.me/lnbits)
- **Documentation**: [LNBits Wiki](https://github.com/lnbits/lnbits/wiki)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Need help?** Open an issue or join the LNBits Telegram group! 
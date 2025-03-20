# Production Deployment Guide

This guide covers deploying the AI-Powered Telegram Assistant to production using Railway for the backend and Vercel for the frontend.

## Prerequisites

- Railway account (https://railway.app)
- Vercel account (https://vercel.app)
- Domain name (for webhook setup)
- Sentry account (for error monitoring)
- Redis Cloud account (for caching and job queue)

## Backend Deployment (Railway)

1. **Prepare Environment Variables**

Create a `.env` file in Railway with these variables:
```env
# Core Configuration
ENVIRONMENT=production
DEBUG=0
ALLOWED_HOSTS=your-domain.com
PORT=8000

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
WEBHOOK_URL=https://your-domain.com/telegram/webhook

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://user:pass@host:port

# AI Services
OPENAI_API_KEY=your_openai_key
ANYTHINGLLM_API_KEY=your_anythingllm_key

# CRM Integration
HUBSPOT_API_KEY=your_hubspot_key
SHOPIFY_ACCESS_TOKEN=your_shopify_token
STRIPE_SECRET_KEY=your_stripe_key

# Social Media
LINKEDIN_ACCESS_TOKEN=your_linkedin_token
TWITTER_API_KEY=your_twitter_key
FACEBOOK_ACCESS_TOKEN=your_facebook_token

# Email & SMS
SENDGRID_API_KEY=your_sendgrid_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

2. **Deploy to Railway**

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Link to existing project
railway link

# Deploy
railway up
```

3. **Configure Domain & SSL**

- Add your domain in Railway dashboard
- Configure DNS records
- Railway handles SSL automatically

4. **Setup Database**

```bash
# Connect to Railway PostgreSQL
railway connect postgresql

# Run migrations
python manage.py migrate
```

5. **Configure Redis**

- Create Redis instance in Redis Cloud
- Add Redis URL to Railway environment variables

6. **Setup Monitoring**

- Configure Sentry DSN in Railway
- Setup Prometheus metrics endpoint
- Configure logging to Railway logs

## Frontend Deployment (Vercel)

1. **Prepare Environment Variables**

Add these to your Vercel project:
```env
NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app
NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn
```

2. **Deploy to Vercel**

```bash
# Login to Vercel
vercel login

# Deploy
vercel --prod
```

3. **Configure Domain**

- Add your domain in Vercel dashboard
- Configure DNS records
- Vercel handles SSL automatically

## Post-Deployment Tasks

1. **Verify Webhook Setup**
```bash
# Set Telegram webhook
curl -F "url=https://your-domain.com/telegram/webhook" \
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

2. **Test Health Check**
```bash
curl https://your-domain.com/health
```

3. **Monitor Initial Logs**
```bash
railway logs
```

4. **Setup Scheduled Tasks**

The scheduler will automatically start with these jobs:
- Social media posting (9 AM, 1 PM, 5 PM)
- Daily analytics reports (8 AM)
- CRM sync (every 30 minutes)
- Lead nurturing (every 15 minutes)
- System health check (every 5 minutes)

## Scaling Configuration

1. **Railway Auto-scaling**

Configure in `railway.toml`:
```toml
[deploy]
numReplicas = 2
healthcheckTimeout = 300
restartPolicyType = "on-failure"
```

2. **Redis Configuration**

Optimize Redis for production:
```python
REDIS_CONFIG = {
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'max_connections': 10,
    'health_check_interval': 30
}
```

3. **Load Balancing**

Railway automatically handles load balancing between replicas.

## Monitoring Setup

1. **Sentry Alerts**

Configure in Sentry dashboard:
- Error thresholds
- Performance monitoring
- Custom alerts

2. **Health Checks**

Monitor these endpoints:
- `/health` - System health
- `/plugins` - Plugin status
- `/metrics` - Prometheus metrics

3. **Logging**

Logs are available in:
- Railway logs dashboard
- Sentry error tracking
- Custom log files

## Backup Strategy

1. **Database Backups**

Railway PostgreSQL automatic backups:
- Daily backups
- 7-day retention
- Point-in-time recovery

2. **Redis Backups**

Redis Cloud handles:
- Automatic backups
- Cross-region replication
- Persistence configuration

## Security Measures

1. **API Security**
- Rate limiting
- JWT authentication
- CORS configuration
- Input validation

2. **Environment Security**
- Secrets management
- SSL/TLS encryption
- Network isolation

3. **Monitoring**
- Failed login attempts
- Unusual traffic patterns
- Error rate spikes

## Troubleshooting

1. **Common Issues**

- Webhook errors:
  ```bash
  # Verify webhook
  curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
  ```

- Database connection issues:
  ```bash
  # Check connection
  railway connect postgresql
  ```

- Redis connection issues:
  ```bash
  # Verify Redis
  redis-cli -u $REDIS_URL ping
  ```

2. **Health Check Failures**

If health check fails:
1. Check logs: `railway logs`
2. Verify services status
3. Check Redis connection
4. Verify plugin status

3. **Performance Issues**

- Monitor Railway metrics dashboard
- Check Sentry performance monitoring
- Analyze Redis usage patterns
- Review database query performance

## Maintenance

1. **Regular Tasks**

- Monitor error rates
- Review performance metrics
- Check system resources
- Update dependencies

2. **Updates**

- Deploy during low-traffic periods
- Use rolling updates
- Maintain backup deployment
- Test in staging first

3. **Backup Verification**

- Regular backup testing
- Recovery procedure verification
- Data integrity checks

## Support

For issues:
1. Check logs in Railway dashboard
2. Review Sentry error reports
3. Check system health endpoint
4. Contact support if needed

Remember to:
- Keep secrets secure
- Monitor system health
- Maintain backups
- Update regularly

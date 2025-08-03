# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated sales reporting Slack bot for Imweb (Korean e-commerce platform). The bot automatically tracks daily sales data for specific products and sends scheduled reports to Slack.

## Key Architecture Components

### Core Classes
- **SalesBot** (`sales_bot.py`): Main bot class that handles sales calculation, report generation, and Slack notifications
- **ImwebTokenManager** (`oauth_token_manager.py`): OAuth token management with automatic refresh capabilities

### Token Management System
The bot uses a sophisticated OAuth token management system:
- Access tokens expire every 2 hours
- Refresh tokens expire every 90 days
- Automatic token refresh happens when access token is within 1.5 hours of expiration
- Monthly automatic refresh schedule (every 30 days at 3:00 AM)
- Token status checks every Monday at 9:00 AM

### Sales Calculation Logic
- Filters orders by target products: `['다이어트의 정석', '벌크업의 정석']`
- Only counts completed payments (`PAYMENT_COMPLETE`, `PARTIAL_REFUND_COMPLETE`)
- Uses actual paid price (after discounts) for calculations
- Supports pagination for large order sets

## Common Development Commands

### Initial Setup (One-time)
```bash
# Install dependencies
pip install -r requirements.txt

# Get initial OAuth token
python3 get_first_token.py
```

### Running the Bot
```bash
# Run the main sales bot
python3 sales_bot.py
```

### Manual Token Management
```bash
# Test token manager independently
python3 oauth_token_manager.py
```

### Testing
- No formal test framework is configured
- Test by running the bot and checking console output
- Verify Slack webhook integration manually

## Configuration

### Environment Setup
- Python 3.9.19 (specified in `runtime.txt`)
- Dependencies: `requests==2.31.0`, `schedule==1.2.0`

### Important Configuration Points
- Slack webhook URL is hardcoded in `sales_bot.py:237` - update before deployment
- Client ID and secret are embedded in the code - consider moving to environment variables for production
- Target products are defined in `SalesBot.__init__()` - modify list as needed

### Deployment
- Configured for cloud deployment (Railway, Render, Google Cloud)
- `Procfile` defines the startup command: `web: python sales_bot.py`
- Bot runs continuously with scheduled tasks

## Scheduled Operations

### Daily Reports
- **12:00**: Midday sales report ("중간")
- **23:59**: Final daily sales report ("최종")

### Maintenance Tasks
- **Monday 09:00**: Token status check
- **Every 30 days at 03:00**: Automatic token refresh

## File Dependencies

### Critical Files
- `imweb_tokens.json`: Auto-generated token storage (never commit to git)
- `sales_bot.py`: Main application entry point
- `oauth_token_manager.py`: Token lifecycle management

### Data Flow
1. `get_first_token.py` → Initial OAuth setup → `imweb_tokens.json`
2. `sales_bot.py` → Uses `ImwebTokenManager` → Accesses Imweb API → Sends to Slack
3. Automatic token refresh maintains continuous operation

## API Integration

### Imweb API Endpoints
- OAuth: `https://openapi.imweb.me/oauth2/`
- Orders: `https://openapi.imweb.me/orders`
- Required scopes: `site-info:write order:read`

### Error Handling
- Automatic retry on token expiration (401 errors)
- Slack notifications for all errors
- Graceful handling of API rate limits and pagination

## Security Considerations

- `imweb_tokens.json` contains sensitive tokens - ensure it's in `.gitignore`
- Slack webhook URL is sensitive - consider environment variables
- Client credentials are embedded - move to secure configuration for production
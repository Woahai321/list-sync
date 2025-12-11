# Configuration Guide

This guide covers all configuration options available in ListSync, from basic setup to advanced features.

## 📋 Table of Contents

1. [Quick Start Configuration](#quick-start-configuration)
2. [Core Configuration](#core-configuration)
3. [List Provider Configuration](#list-provider-configuration)
4. [Advanced Settings](#advanced-settings)
5. [Security Configuration](#security-configuration)
6. [Network Configuration](#network-configuration)
7. [Configuration Examples](#configuration-examples)
8. [Troubleshooting Configuration](#troubleshooting-configuration)

## 🚀 Quick Start Configuration

For a minimal working setup, you only need these essential variables:

```bash
# Copy the sample environment file
cp .env.example .env

# Edit with your details
OVERSEERR_URL=https://your-overseerr-url.com
OVERSEERR_API_KEY=your_overseerr_api_key_here

# Add at least one list
IMDB_LISTS=top
```

## ⚙️ Core Configuration

### Overseerr Connection (Required)

| Variable | Description | Required | Default | Example |
|----------|-------------|----------|---------|---------|
| `OVERSEERR_URL` | Your Overseerr server URL | ✅ | - | `https://overseerr.example.com` |
| `OVERSEERR_API_KEY` | API key from Overseerr settings | ✅ | - | `abc123...` |
| `OVERSEERR_USER_ID` | User ID for making requests | ❌ | `1` | `1` |
| `OVERSEERR_4K` | Send requests as 4K to Overseerr | ❌ | `false` | `true` |

**Getting your API key:**
1. Log into your Overseerr instance
2. Go to Settings → General → API Key
3. Copy the API key and add it to your `.env` file

### Sync Behavior

| Variable | Description | Required | Default | Example |
|----------|-------------|----------|---------|---------|
| `SYNC_INTERVAL` | Hours between automatic syncs | ❌ | `24` | `6` (6 hours) |
| `AUTOMATED_MODE` | Enable automatic syncing | ❌ | `true` | `false` |

**Sync Interval Examples:**
- `24` - Once per day
- `12` - Twice per day  
- `6` - Every 6 hours
- `1` - Every hour
- `0.5` - Every 30 minutes (minimum recommended)
- `0` - Manual sync only

## 📚 List Provider Configuration

### IMDb Lists

Configure IMDb lists using the `IMDB_LISTS` variable (comma-separated):

```bash
IMDB_LISTS=top,boxoffice,moviemeter,tvmeter,ls123456789,ur987654321
```

**Supported IMDb List Types:**

| Type | Format | Description | Example |
|------|--------|-------------|---------|
| **Charts** | `chart_name` | Built-in IMDb charts | `top`, `boxoffice` |
| **User Lists** | `ls` + ID | Public IMDb lists | `ls123456789` |
| **Watchlists** | `ur` + ID | User watchlists | `ur987654321` |
| **Full URLs** | Complete URL | Any IMDb list URL | `https://www.imdb.com/list/ls123456789` |

**Available Charts:**
- `top` - IMDb Top 250 Movies
- `boxoffice` - Box Office
- `moviemeter` - Most Popular Movies
- `tvmeter` - Most Popular TV Shows

### Trakt Lists

Configure Trakt lists and special collections:

```bash
# Regular user lists (numeric IDs)
TRAKT_LISTS=123456,789012

# Special trending/popular lists
TRAKT_SPECIAL_LISTS=trending:movies,popular:shows,anticipated:movies
TRAKT_SPECIAL_ITEMS_LIMIT=50
```

**Regular Trakt Lists:**
- Use numeric list IDs from Trakt URLs
- Example: `https://trakt.tv/lists/123456` → use `123456`

**Special Trakt Lists:**

| Category | Movies | TV Shows |
|----------|--------|----------|
| **Trending** | `trending:movies` | `trending:shows` |
| **Popular** | `popular:movies` | `popular:shows` |
| **Anticipated** | `anticipated:movies` | `anticipated:shows` |
| **Watched** | `watched:movies` | `watched:shows` |
| **Favorited** | `favorited:movies` | `favorited:shows` |

**Special List Settings:**
- `TRAKT_SPECIAL_ITEMS_LIMIT` - Maximum items to fetch from special lists (default: 20)

### Letterboxd Lists

Configure Letterboxd user lists and watchlists:

```bash
LETTERBOXD_LISTS=username/list-name,username/watchlist,another-user/favorites
```

**Letterboxd Format:**
- Format: `username/list-slug`
- Watchlists: `username/watchlist`
- Full URLs are also supported

### MDBList Collections

Configure MDBList collections:

```bash
MDBLIST_LISTS=username/collection-name,top-user/best-movies
```

**MDBList Format:**
- Format: `username/collection-name`
- Extract from URLs like: `https://mdblist.com/lists/username/collection-name`

### Simkl Lists

Configure Simkl user lists and watchlists:

```bash
SIMKL_LISTS=https://simkl.com/5/list/2707-marvel-cinematic-universe-mcu-movies,https://simkl.com/5/list/1234-my-watchlist
```

**Simkl Format:**
- **Full URLs Required**: Simkl lists require complete URLs for proper access
- **User Lists**: `https://simkl.com/5/list/ID-list-name`
- **Watchlists**: `https://simkl.com/5/list/ID-watchlist-name`
- **Collections**: `https://simkl.com/5/list/ID-collection-name`

**Simkl Notes:**
- Always use full URLs (not just IDs)
- Supports both movies and TV shows
- Lists are automatically paginated for large collections

### TVDB Lists

Configure TVDB user favorites and public lists:

```bash
TVDB_LISTS=https://www.thetvdb.com/user/12345/favorites,https://www.thetvdb.com/lists/67890
```

**TVDB Format:**
- **Full URLs Required**: TVDB lists require complete URLs for proper access
- **User Favorites**: `https://www.thetvdb.com/user/USER_ID/favorites`
- **Public Lists**: `https://www.thetvdb.com/lists/LIST_ID`
- **User Lists**: `https://www.thetvdb.com/user/USER_ID/lists/LIST_ID`

**TVDB Notes:**
- Primarily supports TV shows (movies are limited)
- User favorites are the most common use case
- Works with web scraping by default, API key optional for enhanced data

### TMDB Lists

Configure TMDB public lists and collections:

```bash
TMDB_LISTS=https://www.themoviedb.org/list/12345,https://www.themoviedb.org/list/67890-my-favorite-movies
```

**TMDB Format:**
- **Full URLs Required**: TMDB lists require complete URLs for proper access
- **Public Lists**: `https://www.themoviedb.org/list/LIST_ID`
- **User Lists**: `https://www.themoviedb.org/list/LIST_ID-list-name`
- **Collections**: `https://www.themoviedb.org/collection/COLLECTION_ID`

**TMDB Notes:**
- Supports both movies and TV shows
- Works with web scraping by default, API key optional for better performance
- Lists are automatically paginated for large collections

### Steven Lu Lists

Configure Steven Lu's curated popular movies:

```bash
STEVENLU_LISTS=stevenlu
```

**Steven Lu Notes:**
- Only one list available (popular movies)
- Use `stevenlu` as the identifier
- Automatically fetches from the curated JSON endpoint

## 🔑 API Key Configuration

### Optional API Keys for Enhanced Functionality

While ListSync works with web scraping for all providers, API keys provide better performance, reliability, and data quality.

#### Trakt API Key

```bash
TRAKT_CLIENT_ID=your_trakt_client_id_here
```

**Benefits:**
- 10-20x faster than web scraping
- More reliable (no UI changes affect it)
- Better data quality with TMDb IDs and IMDb IDs
- 1000 requests per 5 minutes rate limit

**Setup:**
1. Go to [https://trakt.tv/oauth/applications](https://trakt.tv/oauth/applications)
2. Create new application
3. Copy the Client ID (not the secret)

#### TMDB API Key

```bash
TMDB_KEY=your_tmdb_api_key_here
```

**Benefits:**
- Much faster than web scraping
- More reliable (no UI changes affect it)
- Comprehensive metadata
- 40 requests per 10 seconds rate limit

**Setup:**
1. Go to [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
2. Request API key
3. Copy the API key (v3 auth)

**Note**: TMDB works with web scraping by default. API key is only needed for better performance and reliability.

#### TVDB API Key

```bash
TVDB_KEY=your_tvdb_api_key_here
```

**Benefits:**
- Enhanced data quality
- Better stability
- Access to full TVDB database
- Official API access

**Setup:**
1. Go to [https://thetvdb.com/api-information](https://thetvdb.com/api-information)
2. Register for an account
3. Go to [https://thetvdb.com/dashboard/account/apikey](https://thetvdb.com/dashboard/account/apikey)
4. Create new API key

**Note**: TVDB works perfectly with web scraping. API key is only needed for enhanced metadata.

## 🔧 Advanced Settings

### Notification Configuration

```bash
# Discord webhook for sync notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdef...

# Timezone for scheduling and logs
TZ=GMT
```

**Setting up Discord notifications:**
1. In your Discord server, go to Server Settings → Integrations → Webhooks
2. Create a new webhook for the channel you want notifications in
3. Copy the webhook URL to `DISCORD_WEBHOOK_URL`

**Timezone Configuration:**
- Use standard timezone identifiers (e.g., `GMT+1`, `UTC-5`)
- Affects scheduling and log timestamps
- Default: `GMT`

### Performance Tuning

```bash
# Docker-specific settings (only needed for Docker deployment)
RUNNING_IN_DOCKER=true
NO_SANDBOX=1
DISPLAY=:99
```

These settings are automatically configured in the Docker setup and typically don't need manual adjustment.

## 🔐 Security Configuration

### API Security

```bash
# CORS settings for web interface
CORS_ALLOWED_ORIGINS=http://localhost:3222,https://yourdomain.com

# Frontend/Backend communication
FRONTEND_DOMAIN=http://localhost:3222
BACKEND_DOMAIN=http://localhost:4222
NEXT_PUBLIC_API_URL=http://localhost:4222/api
```

### Credential Storage

ListSync supports two methods for credential storage:

1. **Environment Variables** (Docker, recommended)
2. **Encrypted File Storage** (Manual installation)

For Docker deployments, credentials are stored in environment variables. For manual installations, credentials are encrypted and stored locally with password protection.

## 🌐 Network Configuration

### Docker Networking

```bash
# Frontend (Nuxt 3 Dashboard)
FRONTEND_DOMAIN=http://localhost:3222

# Backend API (FastAPI)  
BACKEND_DOMAIN=http://localhost:4222

# API URL for frontend
NEXT_PUBLIC_API_URL=http://localhost:4222/api

# CORS configuration
CORS_ALLOWED_ORIGINS=http://localhost:3222,http://0.0.0.0:3222,http://127.0.0.1:3222
```

### Port Configuration

Default ports in Docker setup:
- **3222** - Web Dashboard (Nuxt 3 frontend)
- **4222** - API Backend (FastAPI)

To change ports, modify the `docker-compose.yml` file:

```yaml
services:
  listsync-full:
    ports:
      - "8080:3222"  # Map host port 8080 to container port 3222
      - "8081:4222"  # Map host port 8081 to container port 4222
```

## 📝 Configuration Examples

### Basic Home Server Setup

```bash
# Basic configuration for home use
OVERSEERR_URL=http://192.168.1.100:5055
OVERSEERR_API_KEY=your_api_key_here
OVERSEERR_USER_ID=1

# Sync twice daily
SYNC_INTERVAL=12
AUTOMATED_MODE=true

# Popular content lists
IMDB_LISTS=top,boxoffice
TRAKT_SPECIAL_LISTS=trending:movies,popular:shows
TRAKT_SPECIAL_ITEMS_LIMIT=25

# Personal lists
LETTERBOXD_LISTS=yourusername/watchlist

# Timezone
TZ=GMT
```

### Power User Setup

```bash
# Advanced configuration
OVERSEERR_URL=https://overseerr.yourdomain.com
OVERSEERR_API_KEY=your_api_key_here
OVERSEERR_USER_ID=1
OVERSEERR_4K=true

# Frequent syncing
SYNC_INTERVAL=2
AUTOMATED_MODE=true

# Multiple list sources
IMDB_LISTS=top,boxoffice,moviemeter,ls123456789,ur987654321
TRAKT_LISTS=123456,789012
TRAKT_SPECIAL_LISTS=trending:movies,popular:movies,trending:shows,popular:shows,anticipated:movies
TRAKT_SPECIAL_ITEMS_LIMIT=100
LETTERBOXD_LISTS=username/watchlist,username/favorites,friend/recommendations
MDBLIST_LISTS=curator/best-movies,another/sci-fi-collection
STEVENLU_LISTS=stevenlu

# Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TZ=Europe/London

# Custom domains
FRONTEND_DOMAIN=https://listsync.yourdomain.com
BACKEND_DOMAIN=https://listsync-api.yourdomain.com
NEXT_PUBLIC_API_URL=https://listsync-api.yourdomain.com/api
CORS_ALLOWED_ORIGINS=https://listsync.yourdomain.com
```

### Testing/Development Setup

```bash
# Development configuration
OVERSEERR_URL=http://localhost:5055
OVERSEERR_API_KEY=your_dev_api_key

# Minimal sync for testing
SYNC_INTERVAL=0.5
AUTOMATED_MODE=false

# Small test lists
IMDB_LISTS=top
TRAKT_SPECIAL_LISTS=trending:movies
TRAKT_SPECIAL_ITEMS_LIMIT=10

# Debug settings
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🔧 Troubleshooting Configuration

### Validation

ListSync validates your configuration on startup. Common validation errors:

**Missing Required Variables:**
```
Error: OVERSEERR_URL is required
Error: OVERSEERR_API_KEY is required
```

**Invalid Values:**
```
Error: SYNC_INTERVAL must be a positive number
Error: Invalid IMDb list format: invalid_list_id
```

### Testing Configuration

Test your configuration before deploying:

```bash
# Test API connection
curl -H "X-Api-Key: your_api_key" http://your-overseerr-url/api/v1/status

# Validate list URLs
# IMDb: https://www.imdb.com/list/ls123456789
# Trakt: https://trakt.tv/lists/123456
# Letterboxd: https://letterboxd.com/username/list-name
```

### Environment File Location

ListSync looks for environment files in this order:
1. `.env` (recommended)
2. Environment variables set by Docker/system
3. Interactive setup (manual installation only)

### Common Configuration Issues

**List Access Problems:**
- Ensure lists are public, not private
- Verify list URLs are correct and accessible
- Check for typos in list IDs

**Network Issues:**
- Verify Overseerr URL is accessible from ListSync container
- Check firewall settings for Docker networking
- Ensure CORS settings include your domain

**Sync Issues:**
- Start with longer sync intervals (6+ hours) for testing
- Use smaller lists initially to test functionality
- Enable debug logging for detailed error information

### Configuration Best Practices

1. **Start Simple**: Begin with one or two lists to test functionality
2. **Use Appropriate Intervals**: Don't sync more frequently than necessary
3. **Monitor Performance**: Watch for rate limiting or resource issues
4. **Backup Configuration**: Keep a backup of your `.env` file
5. **Test Changes**: Use dry-run mode to test configuration changes
6. **Security**: Keep API keys secure and don't share them publicly

For additional help with configuration, see our [Troubleshooting Guide](troubleshooting.md) or ask for help in our [GitHub Discussions](https://github.com/soluify/list-sync/discussions). 
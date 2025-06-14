# User Guide

This comprehensive guide covers all aspects of using ListSync, from initial setup to advanced configuration and monitoring.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Web Dashboard](#web-dashboard)
3. [List Management](#list-management)
4. [Sync Operations](#sync-operations)
5. [Analytics & Monitoring](#analytics--monitoring)
6. [Configuration Management](#configuration-management)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Getting Started

### First-Time Setup

1. **Install ListSync** following the [Installation Guide](installation.md)
2. **Configure your environment** using the [Configuration Guide](configuration.md)
3. **Start the application** and access the web dashboard

### Quick Start Checklist

- [ ] Overseerr/Jellyseerr URL and API key configured
- [ ] At least one list provider configured (IMDb, Trakt, etc.)
- [ ] Sync interval set to your preference
- [ ] Optional: Discord webhook for notifications
- [ ] Test sync operation completed successfully

## Web Dashboard

The ListSync web dashboard provides a modern, responsive interface for managing all aspects of your sync operations.

### Dashboard Overview

**Main Navigation:**
- **Dashboard** - Overview and quick actions
- **Lists** - Manage your configured lists
- **Analytics** - Sync statistics and performance
- **Activity** - Recent sync operations and logs
- **Settings** - Configuration management

### Key Features

- **Real-time Status Updates** - Live sync progress
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Dark/Light Mode** - Theme selection
- **Interactive Charts** - Visual analytics
- **Quick Actions** - One-click operations

## List Management

### Adding Lists

1. **Navigate to Lists section**
2. **Click "Add New List"**
3. **Select List Type:**
   - IMDb Lists
   - Trakt Lists
   - Letterboxd Lists
   - MDBList Collections
   - Steven Lu Lists

4. **Configure List Details:**

#### IMDb Lists

**Chart Lists:**
```
List ID: top
Description: IMDb Top 250 Movies
```

**User Lists:**
```
List ID: ls123456789
Description: My Watchlist
```

**User Watchlists:**
```
List ID: ur987654321
Description: User's Watchlist
```

#### Trakt Lists

**Regular Lists:**
```
List ID: username/list-name
Description: User's custom list
```

**Special Collections:**
```
List ID: trending:movies
Description: Trending Movies
Limit: 50 (optional)
```

**Popular Collections:**
```
List ID: popular:shows
Description: Popular TV Shows
Limit: 100 (optional)
```

#### Letterboxd Lists

**User Lists:**
```
List ID: username/list-name
Description: User's film list
```

**Watchlists:**
```
List ID: username/watchlist
Description: User's watchlist
```

#### MDBList Collections

**User Collections:**
```
List ID: username/collection-name
Description: Custom collection
```

#### Steven Lu Lists

**Popular Movies:**
```
List ID: stevenlu
Description: Popular movies collection
```

### List Configuration Options

**Sync Settings:**
- **Auto-sync** - Include in automated sync cycles
- **Priority** - Sync order (high, normal, low)
- **4K Requests** - Request 4K versions when available
- **Media Types** - Movies only, TV only, or both

**Advanced Options:**
- **Item Limit** - Maximum items to sync from list
- **Skip Existing** - Skip items already in Overseerr
- **Custom Filters** - Year range, genre filters, etc.

### Managing Existing Lists

**List Actions:**
- **Edit** - Modify list configuration
- **Sync Now** - Trigger immediate sync
- **View Items** - See list contents
- **Disable/Enable** - Toggle list in sync operations
- **Delete** - Remove list from sync

**Bulk Operations:**
- **Select Multiple Lists** - Checkbox selection
- **Bulk Sync** - Sync selected lists
- **Bulk Enable/Disable** - Toggle multiple lists
- **Export Configuration** - Save list configuration

## Sync Operations

### Manual Sync

1. **Single List Sync:**
   - Navigate to Lists
   - Click "Sync Now" on desired list
   - Monitor progress in real-time

2. **Full Sync:**
   - Click "Sync All Lists" button
   - View progress dashboard
   - Receive completion notification

3. **Custom Sync:**
   - Select specific lists
   - Choose sync options
   - Execute custom sync operation

### Automated Sync

**Sync Scheduling:**
- **Interval Configuration** - 30 minutes to 24+ hours
- **Time-based Scheduling** - Specific times of day
- **Conditional Sync** - Based on list changes

**Automated Features:**
- **Smart Retry** - Automatic retry on failures
- **Rate Limiting** - Respectful API usage
- **Error Recovery** - Resume from interruptions
- **Progress Notifications** - Discord/email updates

### Sync Status Monitoring

**Real-time Updates:**
- **Progress Bars** - Visual sync progress
- **Item Counters** - Processed/total items
- **Status Messages** - Current operation details
- **Error Indicators** - Failed items highlighting

**Sync Results:**
- **Success Count** - Successfully requested items
- **Already Available** - Items already in library
- **Already Requested** - Previously requested items
- **Failed Items** - Items that couldn't be processed
- **Skipped Items** - Items excluded by filters

## Analytics & Monitoring

### Dashboard Analytics

**Overview Metrics:**
- **Total Lists** - Number of configured lists
- **Total Items** - All items across lists
- **Success Rate** - Overall sync success percentage
- **Last Sync** - Most recent sync operation

**Performance Metrics:**
- **Average Sync Time** - Time per sync operation
- **Items Per Hour** - Processing rate
- **API Response Time** - Overseerr API performance
- **Error Rate** - Failure percentage

### Detailed Analytics

**Sync History:**
- **Timeline View** - Sync operations over time
- **Success/Failure Trends** - Performance patterns
- **List Performance** - Per-list success rates
- **Media Type Breakdown** - Movies vs TV shows

**Provider Analytics:**
- **Provider Performance** - Success rates by provider
- **Response Times** - Provider response performance
- **Error Patterns** - Common failure reasons
- **Item Distribution** - Content across providers

### Monitoring Alerts

**Notification Settings:**
- **Discord Webhooks** - Rich notifications with embeds
- **Email Alerts** - Simple text notifications
- **Threshold Alerts** - Warnings when metrics exceed limits
- **Schedule Notifications** - Regular status updates

**Alert Types:**
- **Sync Completion** - Operation finished successfully
- **Sync Failures** - Operations that failed
- **High Error Rates** - Unusual failure patterns
- **System Health** - Service availability issues

## Configuration Management

### Environment Configuration

**Core Settings:**
```bash
# Overseerr/Jellyseerr Connection
OVERSEERR_URL=http://your-overseerr-url:5055
OVERSEERR_API_KEY=your-api-key-here
OVERSEERR_USER_ID=1

# Sync Configuration
SYNC_INTERVAL=24
AUTOMATED_MODE=true
OVERSEERR_4K=false
```

**List Configuration:**
```bash
# IMDb Lists (comma-separated)
IMDB_LISTS=top,ls123456789,ur987654321

# Trakt Lists
TRAKT_LISTS=username/watchlist,other/list
TRAKT_SPECIAL_LISTS=trending:movies,popular:shows
TRAKT_SPECIAL_ITEMS_LIMIT=50

# Other Providers
LETTERBOXD_LISTS=username/watchlist
MDBLIST_LISTS=username/collection
STEVENLU_LISTS=stevenlu
```

### Web-based Configuration

**Settings Interface:**
- **Connection Settings** - Overseerr/Jellyseerr configuration
- **Sync Settings** - Intervals and automation
- **Provider Settings** - List configuration
- **Notification Settings** - Discord/email setup
- **Advanced Settings** - Performance tuning

**Configuration Validation:**
- **Connection Testing** - Verify API connectivity
- **List Validation** - Check list accessibility
- **Setting Verification** - Validate configuration values
- **Error Reporting** - Configuration issue alerts

### Backup & Restore

**Configuration Backup:**
- **Export Settings** - Save configuration to file
- **Database Backup** - Backup sync history
- **List Configuration** - Export list settings
- **Schedule Backups** - Automated backup creation

**Configuration Restore:**
- **Import Settings** - Restore from backup file
- **Database Restore** - Restore sync history
- **Selective Restore** - Choose specific settings
- **Validation** - Verify restored configuration

## Troubleshooting

### Common Issues

**Sync Failures:**
1. **Check Overseerr Connection**
   - Verify URL and API key
   - Test connection in settings
   - Check network connectivity

2. **List Access Issues**
   - Verify list URLs/IDs
   - Check provider availability
   - Review privacy settings

3. **Performance Issues**
   - Adjust sync intervals
   - Reduce concurrent operations
   - Monitor resource usage

**Web Dashboard Issues:**
1. **Cannot Access Dashboard**
   - Check port 3222 availability
   - Verify container health
   - Review firewall settings

2. **API Errors**
   - Check backend on port 4222
   - Review API logs
   - Verify database connectivity

### Diagnostic Tools

**Built-in Diagnostics:**
- **System Health Check** - Overall system status
- **Connection Testing** - Test external connections
- **Database Integrity** - Check database health
- **Log Analysis** - Review error patterns

**Log Access:**
- **Web Interface** - View logs in dashboard
- **Container Logs** - Docker container output
- **File Logs** - Persistent log files
- **Structured Logging** - JSON formatted logs

## Best Practices

### List Management

**Organization:**
- **Descriptive Names** - Clear list identification
- **Categorization** - Group related lists
- **Priority Setting** - Important lists first
- **Regular Cleanup** - Remove unused lists

**Performance:**
- **Reasonable Intervals** - Avoid too frequent syncing
- **List Size Management** - Monitor large lists
- **Provider Distribution** - Balance across providers
- **Resource Monitoring** - Watch system resources

### Sync Strategy

**Timing:**
- **Off-peak Hours** - Sync during low usage
- **Staggered Syncing** - Avoid simultaneous operations
- **Maintenance Windows** - Schedule for maintenance
- **User Activity** - Consider user request patterns

**Error Handling:**
- **Monitor Failures** - Watch error rates
- **Retry Logic** - Configure appropriate retries
- **Fallback Plans** - Alternative sync strategies
- **Alert Thresholds** - Set appropriate alert levels

### Security

**API Keys:**
- **Secure Storage** - Use environment variables
- **Regular Rotation** - Update keys periodically
- **Access Monitoring** - Watch for unusual activity
- **Backup Keys** - Keep secure backups

**Network Security:**
- **Firewall Rules** - Restrict unnecessary access
- **HTTPS Usage** - Use secure connections
- **Network Monitoring** - Monitor traffic patterns
- **Update Management** - Keep system updated

### Monitoring

**Regular Checks:**
- **Daily Status** - Check sync operations
- **Weekly Reviews** - Review performance metrics
- **Monthly Analysis** - Analyze trends
- **Quarterly Planning** - Plan improvements

**Alerting:**
- **Critical Alerts** - Immediate attention needed
- **Warning Alerts** - Potential issues
- **Info Notifications** - Status updates
- **Scheduled Reports** - Regular summaries

This user guide provides comprehensive coverage of ListSync functionality. For additional support, refer to the [Troubleshooting Guide](troubleshooting.md) or the [API Documentation](api.md) for advanced usage scenarios. 
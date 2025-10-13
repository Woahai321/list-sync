# ListSync Documentation

Welcome to the comprehensive documentation for ListSync - an automated media list synchronization tool that seamlessly syncs watchlists from various online platforms to your Overseerr or Jellyseerr instance.

## Quick Navigation

### 🚀 Getting Started
- **[Main README](../ReadMe.md)** - Project overview and quick start guide
- **[Installation Guide](installation.md)** - Complete installation instructions
- **[Configuration Guide](configuration.md)** - Detailed configuration setup

### 📚 User Documentation
- **[User Guide](user-guide.md)** - Comprehensive usage guide with examples
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions

### 🔧 Technical Documentation
- **[API Documentation](api.md)** - Complete REST API reference
- **[Architecture Overview](architecture.md)** - Technical architecture and design

### 👥 Developer Resources
- **[Contributing Guide](contributing.md)** - Development setup and contribution workflow

### ⚖️ Legal Information
- **[Legal Disclaimer](legal-disclaimer.md)** - Terms of use and legal information

## Documentation by User Type

### 🏠 Home Users
Perfect for personal media server management:

1. **Start Here**: [Installation Guide](installation.md) - Get ListSync running quickly
2. **Basic Setup**: [Configuration Guide](configuration.md) - Configure your first lists
3. **Daily Use**: [User Guide](user-guide.md) - Master the web dashboard
4. **Need Help?**: [Troubleshooting Guide](troubleshooting.md) - Solve common issues

**Recommended Reading Order:**
1. [ReadMe.md](../ReadMe.md) - Project Overview
2. [installation.md](installation.md) - Installation Guide
3. [configuration.md](configuration.md) - Configuration Setup
4. [user-guide.md](user-guide.md) - Usage Guide

### 🏢 Power Users & System Administrators
For advanced deployments and automation:

1. **Architecture**: [Architecture Overview](architecture.md) - Understand the system design
2. **Advanced Setup**: [Configuration Guide](configuration.md) - Advanced configuration options
3. **API Integration**: [API Documentation](api.md) - Integrate with other systems
4. **Monitoring**: [User Guide](user-guide.md) - Analytics and monitoring features

**Recommended Reading Order:**
1. [architecture.md](architecture.md) - System architecture
2. [installation.md](installation.md) - Installation options
3. [api.md](api.md) - API reference
4. [troubleshooting.md](troubleshooting.md) - Advanced troubleshooting

### 💻 Developers & Contributors
For those wanting to contribute or extend ListSync:

1. **Project Structure**: [Architecture Overview](architecture.md) - Understand the codebase
2. **Development Setup**: [Contributing Guide](contributing.md) - Set up development environment
3. **API Reference**: [API Documentation](api.md) - Understand the API design
4. **Code Standards**: [Contributing Guide](contributing.md) - Coding standards and practices

**Tech Stack:**
- **Backend**: Python 3.9+, FastAPI, SeleniumBase
- **Frontend**: Nuxt 3, Vue 3, TypeScript, Tailwind CSS
- **Database**: SQLite with auto-migrations
- **Deployment**: Docker, Docker Compose

**Recommended Reading Order:**
1. [contributing.md](contributing.md) - Development setup
2. [architecture.md](architecture.md) - Technical architecture
3. [api.md](api.md) - API design
4. [legal-disclaimer.md](legal-disclaimer.md) - Legal considerations

## Documentation by Feature

### 📋 List Management
- **[Configuration Guide](configuration.md#list-providers)** - Configure list providers
- **[User Guide](user-guide.md#list-management)** - Manage lists through web interface
- **[API Documentation](api.md#list-management)** - List management API endpoints

### 🔄 Sync Operations
- **[User Guide](user-guide.md#sync-operations)** - Manual and automated sync
- **[Configuration Guide](configuration.md#sync-configuration)** - Sync intervals and automation
- **[API Documentation](api.md#sync-operations)** - Sync control API endpoints

### 📊 Analytics & Monitoring
- **[User Guide](user-guide.md#analytics--monitoring)** - Dashboard analytics
- **[API Documentation](api.md#analytics)** - Analytics API endpoints
- **[Architecture Overview](architecture.md#monitoring--observability)** - Monitoring architecture

### 🔧 System Administration
- **[Installation Guide](installation.md)** - Deployment options
- **[Configuration Guide](configuration.md)** - System configuration
- **[Troubleshooting Guide](troubleshooting.md)** - System maintenance

## Quick Reference

### Supported List Providers
| Provider | List Types | Example Format |
|----------|------------|----------------|
| **IMDb** | Charts, User Lists, Watchlists | `top`, `ls123456789`, `ur987654321` |
| **Trakt** | Lists, Special Collections | `username/list-name`, `trending:movies` |
| **Letterboxd** | User Lists, Watchlists | `username/list-name` |
| **MDBList** | User Collections | `username/collection-name` |
| **Steven Lu** | Popular Movies | `stevenlu` |

### Common Configuration Examples

**Basic Home Setup:**
```bash
OVERSEERR_URL=http://localhost:5055
OVERSEERR_API_KEY=your-api-key
IMDB_LISTS=top
SYNC_INTERVAL=24
AUTOMATED_MODE=true
```

**Power User Setup:**
```bash
OVERSEERR_URL=https://overseerr.example.com
OVERSEERR_API_KEY=your-api-key
IMDB_LISTS=top,ls123456789,ur987654321
TRAKT_LISTS=username/watchlist,username/favorites
TRAKT_SPECIAL_LISTS=trending:movies,popular:shows
LETTERBOXD_LISTS=username/watchlist
SYNC_INTERVAL=12
OVERSEERR_4K=true
DISCORD_WEBHOOK_URL=your-webhook-url
```

### API Quick Reference

**Base URL:** `http://localhost:4222/api`

**Key Endpoints:**
- `GET /system/health` - System health check
- `GET /lists` - List all configured lists
- `POST /sync/start` - Start manual sync
- `GET /analytics/stats` - Get sync statistics

### Docker Quick Commands

```bash
# Start ListSync
docker-compose up -d

# View logs
docker-compose logs -f

# Update to latest version
docker-compose pull && docker-compose up -d

# Backup data
docker-compose exec listsync-full cp -r /usr/src/app/data /backup/
```

## Troubleshooting Quick Links

### Common Issues
- **[Connection Issues](troubleshooting.md#connection-problems)** - Overseerr/Jellyseerr connectivity
- **[Sync Failures](troubleshooting.md#sync-issues)** - List synchronization problems
- **[Performance Issues](troubleshooting.md#performance-problems)** - Slow sync operations
- **[Web Dashboard Issues](troubleshooting.md#web-interface-issues)** - Dashboard not loading

### Getting Help
1. **Check Documentation** - Search this documentation first
2. **GitHub Issues** - Report bugs or request features
3. **Community Forums** - Ask questions and share experiences
4. **Discord** - Real-time community support (if available)

## Version Information

This documentation is maintained for the latest version of ListSync. For version-specific information:

- **Latest Release** - Check GitHub releases for the most recent version
- **Development** - Follow the `develop` branch for upcoming features
- **Compatibility** - See [Installation Guide](installation.md) for compatibility requirements

## Contributing to Documentation

Help improve this documentation:

1. **Found an Error?** - Open an issue on GitHub
2. **Want to Contribute?** - Follow the [Contributing Guide](contributing.md)
3. **Missing Information?** - Suggest additions or improvements
4. **Translations** - Help translate documentation to other languages

## Legal Notice

By using ListSync and this documentation, you agree to the terms outlined in our [Legal Disclaimer](legal.md). Please read it carefully before using the software.

---

**Last Updated:** This documentation is continuously updated. Check the repository for the most recent version.

**Need Help?** If you can't find what you're looking for, check the [Troubleshooting Guide](troubleshooting.md) or open an issue on GitHub. 
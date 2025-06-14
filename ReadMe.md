# 🍿 ListSync - Bridge Your Watchlist & Media Server 🎬

![ListSync Logo](https://share.woahlab.com/-Tdgu2viusH)
![GitHub last commit](https://img.shields.io/github/last-commit/woahai321/list-sync?style=for-the-badge&logo=github)
![GitHub issues](https://img.shields.io/github/issues/woahai321/list-sync?style=for-the-badge&logo=github)
![GitHub stars](https://img.shields.io/github/stars/woahai321/list-sync?style=for-the-badge&logo=github)
![GitHub release](https://img.shields.io/github/v/release/woahai321/list-sync?style=for-the-badge&logo=github)
![Docker](https://img.shields.io/badge/Docker-ready-blue?style=for-the-badge&logo=docker)
![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python)
[![Website](https://img.shields.io/badge/Website-soluify.com-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)](https://soluify.com/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/company/soluify)

---

## 🚀 What is ListSync? 

ListSync automatically syncs your watchlists from IMDb, Trakt, Letterboxd, MDBList, and more with Overseerr/Jellyseerr. No more manual adding - just add movies and shows to your favorite watchlist, and they'll appear in your media server automatically.

Key Features:

- 🔄 Automatic synchronization
- 🎬 Support for multiple watchlist platforms
- 🖥️ Compatible with Overseerr and Jellyseerr
- ⚡ Easy setup with Docker

---

## 📚 Quick Links

- [🚀 Installation Guide](#-getting-started)
- [📋 List Setup Guide](#-obtaining-list-ids)
- [🛠️ Troubleshooting](#-troubleshooting)
- [📖 Documentation](docs/)

---

## 🖥️ Modern Web Dashboard

ListSync now includes a **comprehensive web dashboard** built with Next.js 15 and React 19, providing a modern interface to manage all your sync operations.

![ListSync Web Dashboard](https://share.woahlab.com/-Znz4vjsvyW)

### **Key Features**
- 📊 **Real-Time Sync Monitoring** - Live progress bars and status updates
- 📋 **Intuitive List Management** - Add, edit, and organize your lists with ease
- 📈 **Comprehensive Analytics** - Success rates, performance metrics, and historical data
- ⚙️ **Web-Based Configuration** - Manage lists through the dashboard

---

## ✨ Run ListSync & SeerrBridge with ElfHosted 🚀

[ElfHosted](https://store.elfhosted.com/product/list-sync/elf/6929/) is your friendly neighborhood [open-source](https://elfhosted.com/open/) PaaS, handling the geeky heavy-lifting (_hosting, security, updates, you name it!_) so you can focus on watching your media.

> [!IMPORTANT]
> **ElfHosted 💜 ListSync & SeerrBridge!**
>
> [ListSync](https://store.elfhosted.com/product/list-sync/elf/6929/) and its awesome companion [SeerrBridge](https://store.elfhosted.com/seerrbridge/elf/6929/) are fully supported and integrated into the ElfHosted ecosystem, you can already get them pre-configured in the bundles below, with a $1, 7-day trial!

> [!TIP]
> **ElfHosted Streaming Bundles: Your Turn-Key Streaming Powerhouse!** 💹
>
> Want all of this without the DIY setup? 🎉 These ElfHosted bundles come pre-wired with RealDebrid, SeerrBridge and ListSync, and your choice of media server. Get the ultimate hassle-free, automated infinite streaming experience:
> * [Starter](https://store.elfhosted.com/product/starter/elf/6929/)  Personal Media Streamer [2xHD / 1x4K, contented]
> * [Hobbit](https://store.elfhosted.com/product/hobbit/elf/6929/) Personal Media Streamer [4xHD / 2x4K, semi-dedicated]
> * [Ranger](https://store.elfhosted.com/product/ranger/elf/6929/) Personal Media Streamer [8xHD / 4x4K, semi-dedicated]
---

## 🚀 Getting Started

ListSync offers **flexible deployment options** to suit different use cases, from quick testing to full production deployments with web dashboard.

## 🐳 Deployment Options

<details>
<summary>📦 Full Stack Deployment (Recommended)</summary>

### **Complete ListSync with Web Dashboard + API + Core Sync**

The **full deployment** includes everything: the core sync engine, REST API backend, and modern web dashboard for comprehensive management.

**What's Included:**
- 🖥️ **Web Dashboard** (Port 3222) - Modern React interface
- 🔌 **REST API** (Port 4222) - Full API for automation
- ⚙️ **Core Sync Engine** - Automated list synchronization
- 📊 **Real-time Monitoring** - Live sync progress and analytics
- 🎛️ **Configuration Management** - Web-based settings

**Deploy with Docker Compose:**
```bash
# Copy the example environment file and configure
cp .env.example .env
# Edit .env with your settings, then start using the public image
docker-compose up -d
# or build from source
docker-compose -f docker-compose.local.yml up -d
```

**Access Points:**
- 🌐 **Web Dashboard:** http://localhost:3222
- 🔗 **API Docs:** http://localhost:4222/docs
- 📊 **Health Check:** http://localhost:4222/api/system/health

</details>

<details>
<summary>⚙️ Core-Only Deployment</summary>

### **Lightweight Core Sync Engine Only**

Perfect for **headless servers** or when you only need the core synchronization functionality without the web interface.

**What's Included:**
- ⚙️ **Core Sync Engine** - Automated list synchronization only
- 📝 **Console Logging** - Text-based status updates
- 🔄 **Scheduled Syncing** - Automated intervals
- 💾 **Local Database** - SQLite for sync history

**Deploy with Docker Compose:**
```bash
# Copy the core environment file and configure
cp .env.core .env
# Edit .env with your settings, then start
docker-compose -f docker-compose.core.yml up -d
```

**Perfect for:**
- 🖥️ Headless servers
- 📦 Minimal resource usage
- 🔧 Integration with existing systems
- 🚀 Lightweight automation

</details>

<details>
<summary>🌐 Public Domain Deployment</summary>

### **Internet-Accessible Deployment with Domain**

Deploy ListSync with **public internet access** using your own domain, perfect for remote management and team access.

**Deploy with Docker Compose:**
```bash
# Copy the domain environment file and configure
cp .env.proddomain .env
# Edit .env with your domain settings, then start
docker-compose -f docker-compose.proddomain.yml up -d
```

</details>


## 🛠️ Configuration Setup

All deployment options use the same **environment configuration**. Create a `.env` file or use our plug-and-play template:

**Quick Start with Pre-configured Lists**: Use our plug-and-play configuration:

```bash
# Copy the plug-and-play environment file
cp .env.plugnplay .env
# Edit only the essential settings in .env:
# - OVERSEERR_URL (your Overseerr/Jellyseerr URL)
# - OVERSEERR_API_KEY (your API key)
# - DISCORD_WEBHOOK_URL (optional)
# - TZ (your timezone)
```

The `.env` file comes pre-configured with curated lists including:

| Provider | List Type | Description |
|----------|-----------|-------------|
| **IMDb** | Chart & Lists | [Top 250 Movies](https://www.imdb.com/chart/top), [Disney Movies](https://www.imdb.com/list/ls026785255) |
| **Trakt** | Trending & Popular | [Trending Movies](https://trakt.tv/movies/trending), [Popular Movies](https://trakt.tv/movies/popular), [Trending Shows](https://trakt.tv/shows/trending), [Popular Shows](https://trakt.tv/shows/popular) |
| **MDBList** | Curated Collections | [Top Weekly Movies](https://mdblist.com/lists/garycrawfordgc/top-movies-of-the-week), [Pixar Movies](https://mdblist.com/lists/linaspurinis/pixar-movies), [Pirated Movies Charts](https://mdblist.com/lists/hdlists/top-ten-pirated-movies-of-the-week-torrent-freak-com) |
| **Steven Lu** | Popular Collection | [Popular Movies Collection](https://movies.stevenlu.com/) |

### 🌍 Timezone Configuration

ListSync automatically timestamps all sync activities and displays them in the web interface. To ensure timestamps match your local time, configure your timezone using the examples below.

<details>
<summary>🕐 Setting Your Timezone</summary>

#### **Quick Setup by Timezone**

Choose your timezone using either **UTC offset** or **regional timezone** format:

##### **🌍 UTC Offset Format (Universal)**
```yaml
# docker-compose.yml
environment:
  # UTC offsets (recommended for simplicity)
  - TZ=UTC+0 # Greenwich Mean Time
  - TZ=UTC-5 # US Eastern Time
  - TZ=UTC-6 # US Central Time
  - TZ=UTC-7 # US Mountain Time
  - TZ=UTC-8 # US Pacific Time
  - TZ=UTC+1 # Central European Time
  - TZ=UTC+2 # Eastern European Time
  - TZ=UTC+8 # China/Singapore Time
  - TZ=UTC+9 # Japan/Korea Time
  - TZ=UTC+10 # Eastern Australia Time

#### **Finding Your Timezone**

- **🌐 Online**: Visit [timeanddate.com/time/zones](https://www.timeanddate.com/time/zones/) for the complete worldwide list of offsets
- **🖥️ Linux/macOS**: Run `timedatectl` or `cat /etc/timezone`
- **🪟 Windows**: Check "Time zone" in Settings → Time & Language

</details>
</details>

## 🛠️ Manual Installation (Advanced Users)

<details>
<summary>🔧 Local Development & Manual Setup</summary>

For **developers** or **advanced users** who want to run ListSync without Docker or need a **development environment**.

### **Prerequisites**
- Python 3.9+
- Node.js 18+ (for web dashboard)
- Chrome/Chromium browser
- Git

### **Quick Manual Setup**

| Installation Method | Command |
| :------------------ | :------------------------------------------------------------ |
| ![Poetry](https://img.shields.io/badge/Poetry-ready-blue?style=for-the-badge&logo=poetry) | `git clone https://github.com/Woahai321/list-sync.git && cd list-sync && poetry install && poetry run python -m list_sync` |
| ![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python) | `git clone https://github.com/Woahai321/list-sync.git && cd list-sync && pip install -r requirements.txt && python -m list_sync` |

**Additional Resources:**
- 📖 [Detailed Installation Guide](docs/installation.md)
- 👥 [Contributing Guide](docs/contributing.md)
- 🏗️ [Architecture Overview](docs/architecture.md)

</details>

---

### Currently in Development for v0.7.0

For the most stable experience, use the source code from the latest release [here](https://github.com/Woahai321/list-sync/releases/tag/v0.6.0).

---
## 📊 Compatibility

<details>
<summary>🌉 SeerrBridge Integration</summary>


[![SeerrBridge](https://img.shields.io/badge/SeerrBridge-Compatible-blue?style=for-the-badge&logo=github)](https://github.com/Woahai321/SeerrBridge)

SeerrBridge is our companion application that provides an alternative to traditional \*arr stack (Radarr/Sonarr) setup. It works alongside ListSync to create a complete media management solution:

- **Automated Processing**: When ListSync adds requests to Jellyseerr/Overseerr, SeerrBridge automatically processes them
- **Browser Automation**: Uses Selenium to automate media fetching through Debrid Media Manager
- **Simplified Setup**: Eliminates the need for complex \*arr stack configuration

#### How ListSync & SeerrBridge Work Together

1. ListSync adds media requests to Jellyseerr/Overseerr
2. SeerrBridge detects the requests via webhook
3. SeerrBridge automatically processes the requests through DMM
4. Media becomes available in your RD library

For detailed information about SeerrBridge, visit the [SeerrBridge Repository](https://github.com/Woahai321/SeerrBridge).
</details>

### Media Server Compatibility

|                                                                                                                                                                                                                                                                                     Application                                                                                                                                                                                                                                                                                     |    Status    | Notes                              |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :----------: | :--------------------------------- |
|  ![Overseerr](https://img.shields.io/badge/Overseerr-1.33.2+-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)   | ✅ Supported | Full functionality with Overseerr  |
| ![Jellyseerr](https://img.shields.io/badge/Jellyseerr-1.9.2+-purple?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Full functionality with Jellyseerr |
|    ![Radarr](https://img.shields.io/badge/Radarr-5.11.0+-orange?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)     | ✅ Supported | Compatible through Jellyseerr      |
|     ![Sonarr](https://img.shields.io/badge/Sonarr-4.0.9+-5cad7b?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)     | ✅ Supported | Compatible through Jellyseerr      |

### Supported List Services

|                                                                                                                                                                                                                                                                                   Service                                                                                                                                                                                                                                                                                   |    Status    | Notes                                                        |
| :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :----------: | :----------------------------------------------------------- |
|       ![IMDB](https://img.shields.io/badge/IMDB-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)       | ✅ Supported | Full support for lists, watchlists, and charts              |
|      ![Trakt](https://img.shields.io/badge/Trakt-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)      | ✅ Supported | Full support for lists and user watchlists                  |
| ![Trakt Special](https://img.shields.io/badge/Trakt_Special-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Special lists include trending, popular, anticipated (configurable item limit) |
| ![Letterboxd](https://img.shields.io/badge/Letterboxd-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Fixed pagination for watchlists with "Older" button support |
|     ![MDBList](https://img.shields.io/badge/MDBList-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)     | ✅ Supported | Support for username/listname format or full URLs          |
|   ![Steven Lu](https://img.shields.io/badge/Steven_Lu-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)   | ✅ Supported | Popular movies from JSON API  |

---

## 📋 Obtaining List IDs

ListSync supports multiple list services. You can add them using either the raw URL or the list ID.

<details>
<summary>📋 IMDb List ID or URL</summary>

#### **Using the Raw URL**:
1. Navigate to your IMDb list in your browser.  
2. Copy the URL from the address bar. Examples:  
   - Custom lists: `https://www.imdb.com/list/ls012345678/`  
   - IMDb charts: `https://www.imdb.com/chart/top/` (Top 250), `https://www.imdb.com/chart/boxoffice/` (Box Office)  
   - Watchlists: `https://www.imdb.com/user/ur12345678/watchlist`  
3. Paste the URL directly into ListSync.

#### **Using the List ID**:
1. Look at the URL:  
   - Custom lists: `ls012345678`  
   - IMDb charts: Use the chart name (e.g., `top`, `boxoffice`)  
   - Watchlists: `ur12345678`  
2. Use the list ID in ListSync.

#### **Supported IMDb Charts**:
- `top` (Top 250 Movies)  
- `boxoffice` (Box Office)  
- `moviemeter` (MovieMeter)  
- `tvmeter` (TVMeter)  
</details>

<details>
<summary>📋 Trakt List ID or URL</summary>

#### **Using the Raw URL**:
1. Navigate to your Trakt list in your browser.  
2. Copy the URL from the address bar. Example:  
   - `https://trakt.tv/users/username/lists/example-list`  
3. Paste the URL directly into ListSync.

#### **Using the List ID**:
1. Click the "Share" button on your Trakt list.  
2. Copy the link, which will look like:  
   - `https://trakt.tv/lists/12345678`  
3. The list ID is the number at the end (e.g., `12345678`).  
</details>

<details>
<summary>📋 Trakt Special Lists</summary>

#### **Using the Raw URL**:
1. Copy the URL from the address bar. Examples:
   - `https://trakt.tv/movies/trending`
   - `https://trakt.tv/shows/popular`
   - `https://trakt.tv/movies/boxoffice`

#### **Using Shortcut Format**:
ListSync supports a shortcut format of `list-type:media-type`. Examples:
- `trending:movies` - Top trending movies
- `popular:shows` - Popular TV shows
- `anticipated:movies` - Most anticipated movies

#### **Available Types**:
- **List types**: trending, popular, anticipated, watched, collected, boxoffice, streaming, recommendations, favorited 
- **Media types**: movies, shows

Note: The boxoffice list type is only available for movies.

These special lists sync a configurable number of items (default: 20, can be set via TRAKT_SPECIAL_ITEMS_LIMIT environment variable).
</details>

<details>
<summary>📋 Letterboxd URL</summary>

#### **Using the Raw URL**:
1. Navigate to your Letterboxd list in your browser.  
2. Copy the URL from the address bar. Example:  
   - `https://letterboxd.com/user/list/example-list/`  
   - `https://letterboxd.com/user/watchlist/` (for watchlists)
3. Paste the URL directly into ListSync.  
</details>

<details>
<summary>📋 MDBList URL or Username/List Format</summary>

#### **Using the Raw URL**:
1. Navigate to your MDBList list in your browser.
2. Copy the URL from the address bar. Example:
   - `https://mdblist.com/lists/username/listname`
3. Paste the URL directly into ListSync.

#### **Using Username/List Format**:
1. You can also use the simpler format:
   - `username/listname`
2. ListSync will automatically expand this to the full URL.
</details>

<details>
<summary>📋 Steven Lu's Popular Movies</summary>

This is a curated list of popular movies maintained by Steven Lu, available at:
- `https://s3.amazonaws.com/popular-movies/movies.json`

To enable this list, simply add the below vairable:
- `STEVENLU_LISTS=stevenlu`

This will be recognized as the Steven Lu Popular Movies list.
</details>

---

## 📋 Notes

- **Security Best Practices:** Please read scripts you find online before running them.
- **API Credentials:** Always keep your API credentials secure.
- **Rate Limiting:** Be mindful of Overseerr's rate limiting policies during imports.
- **Permissions:** Only import and manage media you have the rights to handle.

## 💰 Support ListSync's Development

If you find ListSync useful and would like to support its development, consider becoming a sponsor:

➡️ [Sponsor us on GitHub](https://github.com/sponsors/Woahai321)

Thank you for your support!

---

## 📖 Documentation

For comprehensive documentation, visit our [Documentation Hub](/docs/index.md) or explore specific guides:

- **[User Guide](/docs/user-guide.md)** - Complete usage guide with examples
- **[Installation Guide](/docs/installation.md)** - Detailed installation instructions
- **[Configuration Guide](/docs/configuration.md)** - Environment setup and configuration
- **[API Documentation](/docs/api.md)** - Complete REST API reference
- **[Architecture Overview](/docs/architecture.md)** - Technical architecture and design

## 🛠 Troubleshooting

If you encounter any issues while using ListSync, please check our [Troubleshooting Guide](/docs/troubleshooting.md) for solutions to common problems.

## 🤝 Contributing

We welcome contributions! For guidelines on how to contribute, please see our [Contributing Guide](/docs/contributing.md).

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/license/mit). Review the LICENSE file for more details.

## 🛡️ Legal Information

For important legal information about using ListSync, please refer to our [Legal Disclaimer](/docs/legal.md).

## Star History

<a href="https://www.star-history.com/#Woahai321/list-sync&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Woahai321/list-sync&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Woahai321/list-sync&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Woahai321/list-sync&type=Date" />
 </picture>
</a>
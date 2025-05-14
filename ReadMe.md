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

ListSync automatically syncs your watchlists from IMDb, Trakt, and Letterboxd with Overseerr/Jellyseerr. No more manual adding - just add movies and shows to your favorite watchlist, and they'll appear in your media server automatically.

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
> * [Starter](https://store.elfhosted.com/product/hobbit/elf/6929/)  Personal Media Streamer [2xHD / 1x4K, contented]
> * [Hobbit](https://store.elfhosted.com/product/starter/elf/6929/) Personal Media Streamer [4xHD / 2x4K, semi-dedicated]
> * [Ranger](https://store.elfhosted.com/product/ranger/elf/6929/) Personal Media Streamer [8xHD / 4x4K, semi-dedicated]
---
## 🎬 Demo

![Bot In Action](https://share.woahlab.com/-BZtwSD96LN)
---

## 🚀 Getting Started

You can run ListSync in two primary modes: **Interactive Mode** and **Automated Mode**. 

### 1. **Interactive Mode** (Recommended for Quick Start)

The quickest way to get started is by using our Docker one-liner, which runs ListSync in Interactive Mode. This option will prompt you for all the necessary information during setup:

| Installation Method | Command |
| :-------------------- | :---------------------------------- |
| ![Docker](https://img.shields.io/badge/Docker-ready-blue?style=for-the-badge&logo=docker) | `docker pull ghcr.io/woahai321/list-sync:main && docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main` |

### 2. **Automated Mode** (Preferred for Regular Syncing)

For a seamless experience, you can run ListSync in Automated Mode using a .env file and Docker Compose. This mode eliminates the need for manual inputs each time you run the script by automatically pulling list IDs and configurations from your `.env` file:

<details>
<summary>Expand for Docker Compose Instructions 🐳</summary>

#### Running with Docker Compose

**Create a `.env` file**: Configure your settings in a `.env` file with the following template:

```env
# Overseerr Configuration 
OVERSEERR_URL=https://your-overseerr-instance
OVERSEERR_API_KEY=your-api-key-here
OVERSEERR_USER_ID=1

# Set to true for automated mode (recommended for Docker)
AUTOMATED_MODE=true

# Sync interval in hours (default: 24)
SYNC_INTERVAL=24

# Request Quality Profile (true for 4K, false for standard)
OVERSEERR_4K=false

# Lists Configuration (comma-separated)
# Examples:
IMDB_LISTS=ls123456789,ur123456789,top,boxoffice,https://www.imdb.com/list/ls123456789/
TRAKT_LISTS=12345,67890,https://trakt.tv/users/username/lists/listname
LETTERBOXD_LISTS=https://letterboxd.com/username/list/listname/ 
```

**Create a `docker-compose.yml` file**:

```
version: "3.8"

services:
  listsync:
    image: ghcr.io/woahai321/list-sync:main
    container_name: listsync
    environment:
      - OVERSEERR_URL=${OVERSEERR_URL}
      - OVERSEERR_API_KEY=${OVERSEERR_API_KEY}
      - OVERSEERR_USER_ID=${OVERSEERR_USER_ID:-1}
      - SYNC_INTERVAL=${SYNC_INTERVAL:-24}
      - AUTOMATED_MODE=true
      - OVERSEERR_4K=${OVERSEERR_4K:-false}
      - IMDB_LISTS=${IMDB_LISTS}
      - TRAKT_LISTS=${TRAKT_LISTS}
      - LETTERBOXD_LISTS=${LETTERBOXD_LISTS}
    volumes:
      - ./data:/usr/src/app/data
      - ./.env:/usr/src/app/.env
    restart: unless-stopped
```

**Run using Docker Compose**:
| Installation Method | Command |
| :----------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| ![Docker](https://img.shields.io/badge/Docker-ready-blue?style=for-the-badge&logo=docker) | `docker-compose up` |


This setup will trigger *Automated Mode*, meaning it will automatically pull in the added lists based on your configuration, streamlining the syncing process.
</details>

### 3. **Manual Installation** (Advanced Users)

You can also set up ListSync manually if you prefer a more hands-on approach:

<details>
<summary>Expand for Manual Installation Instructions 🛠️</summary>

#### Manual Installation Methods

| Installation Method | Command |
| :------------------ | :------------------------------------------------------------ |
| ![Poetry](https://img.shields.io/badge/Poetry-ready-blue?style=for-the-badge&logo=poetry) | `git clone https://github.com/Woahai321/list-sync.git && cd list-sync && poetry install && poetry run python add.py` |
| ![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python) | `git clone https://github.com/Woahai321/list-sync.git && cd list-sync && pip install -r requirements.txt && python add.py` |

Refer to our [Installation Guide](/docs/installation.md) for detailed instructions.
</details>

---

### Currently in Development for v0.6.0

For the most stable experience, use the source code from the latest release [here](https://github.com/Woahai321/list-sync/releases/tag/v0.5.6).

<details>
<summary>How Does It Work?</summary>

ListSync seamlessly syncs your watchlists with your media server in three simple steps:

#### 1. **Fetch Watchlists**

ListSync retrieves your watchlists from **IMDb**, **Trakt** or **Letterboxd** using Selenium web scraping techniques.

#### 2. **Search Media on Media Server**

ListSync searches for each item on your media server (**Overseerr** or **Jellyseerr**) using its API. It handles edge cases like special characters or multiple results for accurate matches.

#### 3. **Request Media**

ListSync checks if the media is already available or requested. If not, it automatically requests the item:

- For **Movies**, it requests the title.
- For **TV Shows**, it requests all available seasons.
</details>
<details>
<summary>Why Use ListSync?</summary>

- **Save Time**: Automates adding movies and TV shows to your media server.
- **Stay Organized**: Keeps your media server in sync with your watchlists.
- **Flexible**: Works with IMDb, Trakt, Letterboxd, Overseerr, and Jellyseerr.
- **Customizable**: Set sync intervals to match your preferences.
</details>

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

|                                                                                                                                                                                                                                                                                   Service                                                                                                                                                                                                                                                                                   |    Status    | Notes               |
| :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :----------: | :------------------ |
|       ![IMDB](https://img.shields.io/badge/IMDB-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)       | ✅ Supported | Currently supported |
|      ![Trakt](https://img.shields.io/badge/Trakt-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)      | ✅ Supported | Currently supported |
| ![Letterboxd](https://img.shields.io/badge/Letterboxd-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Currently supported |

---

## 📋 Obtaining List IDs

ListSync supports **IMDb**, **Trakt**, and **Letterboxd** lists. You can add them using either the raw URL or the list ID.

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
<summary>📋 Letterboxd URL</summary>

#### **Using the Raw URL**:
1. Navigate to your Letterboxd list in your browser.  
2. Copy the URL from the address bar. Example:  
   - `https://letterboxd.com/user/list/example-list/`  
3. Paste the URL directly into ListSync.  
</details>

### Adding Multiple List IDs

When inputting list IDs or URLs, you can add multiple lists by separating them with commas:

- Example: `ls012345678,12345678,https://www.imdb.com/chart/top/,ur987654321,https://letterboxd.com/user/list/example-list/`

This allows you to sync multiple lists at once, whether they are custom lists, charts, or watchlists.

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

## 🔎 How it Works

For detailed information on how ListSync works, please refer to our [How it Works](/docs/how-it-works.md) document.

## 🛠 Troubleshooting

If you encounter any issues while using ListSync, please check our [Troubleshooting Guide](/docs/troubleshooting.md) for solutions to common problems.

## 🛤️ Roadmap

To see our plans for future development and features, visit our [Roadmap](/docs/roadmap.md).

## 🤝 Contributing

We welcome contributions! For guidelines on how to contribute, please see our [Contributing Guide](/docs/contributing.md).

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/license/mit). Review the LICENSE file for more details.

## 🛡️ Legal Disclaimer

For important legal information about using ListSync, please refer to our [Legal Disclaimer](/docs/legal-disclaimer.md).

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Woahai321/list-sync&type=Date)](https://star-history.com/#Woahai321/list-sync&Date)

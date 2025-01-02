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

ListSync is a powerful tool designed to bridge your watchlists from platforms like IMDb and Trakt with your media server (Overseerr or Jellyseerr). It automatically syncs your designated watchlists, ensuring that your media server is always up-to-date with the movies and TV shows you want to watch. ListSync eliminates the manual effort of adding items to your media server, filling a hole in the jellyfine pipeline, making it easier to manage your media library.

### How Does It Work?  

ListSync seamlessly syncs your watchlists with your media server in three simple steps:  

#### 1. **Fetch Watchlists**  
ListSync retrieves your watchlists from **IMDb** or **Trakt** using web scraping techniques:  
- **IMDb Lists**: Supports list IDs (e.g., `ls123456789`), URLs, and charts like Top 250, Box Office, MovieMeter, and TVMeter.  
- **Trakt Lists**: Fetches lists using IDs or URLs, ensuring all items are retrieved regardless of size.  

#### 2. **Search Media on Media Server**  
ListSync searches for each item on your media server (**Overseerr** or **Jellyseerr**) using its API. It handles edge cases like special characters or multiple results for accurate matches.  

#### 3. **Request Media**  
ListSync checks if the media is already available or requested. If not, it automatically requests the item:  
- For **movies**, it requests the title.  
- For **TV shows**, it requests all available seasons.  

### Why Use ListSync?  
- **Save Time**: Automates adding movies and TV shows to your media server.  
- **Stay Organized**: Keeps your media server in sync with your watchlists.  
- **Flexible**: Works with IMDb, Trakt, Overseerr, and Jellyseerr.  
- **Customizable**: Set sync intervals to match your preferences.  

### Currently in Development for v0.6.0  
For the most stable experience, use the source code from the latest release [here](https://github.com/Woahai321/list-sync/releases/tag/v0.5.3).  

## 🎬 Demo

![Bot In Action](https://share.woahlab.com/-BZtwSD96LN)

---

## 🚀 Getting Started

|                                    Installation Method                                     |                                                                             Command                                                                              |
| :----------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| ![Docker](https://img.shields.io/badge/Docker-ready-blue?style=for-the-badge&logo=docker)  | `docker pull ghcr.io/woahai321/list-sync:main && docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main` |
| ![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python) |                    `git clone https://github.com/Woahai321/list-sync.git && cd list-sync && pip install -r requirements.txt && python add.py`                    |
| ![Poetry](https://img.shields.io/badge/Poetry-ready-blue?style=for-the-badge&logo=poetry)  |                       `git clone https://github.com/Woahai321/list-sync.git && cd list-sync && poetry install && poetry run python add.py`                       |

For detailed installation instructions, please refer to our [Installation Guide](/docs/installation.md).

---

## 📊 Compatibility

|                                                                                                                                                                                                                                                                                     Application                                                                                                                                                                                                                                                                                     |    Status    | Notes                              |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :----------: | :--------------------------------- |
|                                                                                                                                                                                                                [![SeerrBridge](https://img.shields.io/badge/SeerrBridge-Compatible-blue?style=for-the-badge&logo=github)](https://github.com/Woahai321/SeerrBridge)                                                                                                                                                                                                                 | ✅ Supported | Fully compatible                   |
|  ![Overseerr](https://img.shields.io/badge/Overseerr-1.33.2+-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)   | ✅ Supported | Full functionality with Overseerr  |
| ![Jellyseerr](https://img.shields.io/badge/Jellyseerr-1.9.2+-purple?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Full functionality with Jellyseerr |
|    ![Radarr](https://img.shields.io/badge/Radarr-5.11.0+-orange?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)     | ✅ Supported | Started with supporting movies     |
|     ![Sonarr](https://img.shields.io/badge/Sonarr-4.0.9+-5cad7b?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)     | ✅ Supported | Now also supports TV shows         |

### Supported List Services

|                                                                                                                                                                                                                                                                              Service                                                                                                                                                                                                                                                                              |    Status    | Notes               |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :----------: | :------------------ |
|  ![IMDB](https://img.shields.io/badge/IMDB-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==)  | ✅ Supported | Currently supported |
| ![Trakt](https://img.shields.io/badge/Trakt-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Currently supported |

## 🔍 Obtaining List IDs

ListSync supports both IMDb and Trakt lists, and you can add them using either the raw URL or the list ID. This flexibility allows you to simply copy and paste from your browser’s URL bar or follow the instructions below to extract the list ID. Additionally, ListSync now supports IMDb charts, making it even easier to sync popular lists like the Top 250 or Box Office.

### IMDb List ID or URL

You can add IMDb lists using either the raw URL or the list ID. Here’s how:

#### **Using the Raw URL**:

1. Navigate to your IMDb list in your browser.
2. Copy the URL from the address bar. It will look like one of the following:
   - For custom lists: `https://www.imdb.com/list/ls012345678/`
   - For IMDb charts: `https://www.imdb.com/chart/top/` (Top 250), `https://www.imdb.com/chart/boxoffice/` (Box Office), etc.
   - For watchlists: `https://www.imdb.com/user/ur12345678/watchlist`
3. Paste the URL directly into ListSync.

#### **Using the List ID**:

1. Navigate to your IMDb list in your browser.
2. Look at the URL. It will be in one of the following formats:
   - For custom lists: `https://www.imdb.com/list/ls012345678/` → The list ID is `ls012345678`.
   - For IMDb charts: The chart name (e.g., `top`, `boxoffice`, `moviemeter`, `tvmeter`) is the list ID.
   - For watchlists: `https://www.imdb.com/user/ur12345678/watchlist` → The list ID is `ur12345678`.
3. Use the list ID in ListSync.

#### **Supported IMDb Charts**:

ListSync supports the following IMDb charts by name:

- `top` (Top 250 Movies)
- `boxoffice` (Box Office)
- `moviemeter` (MovieMeter)
- `tvmeter` (TVMeter)

### Trakt List ID or URL

You can add Trakt lists using either the raw URL or the list ID. Here’s how:

#### **Using the Raw URL**:

1. Navigate to your Trakt list in your browser.
2. Copy the URL from the address bar. It will look like one of the following:
   - For public lists: `https://trakt.tv/lists/12345678`
   - For user lists: `https://trakt.tv/users/username/lists/12345678`
3. Paste the URL directly into ListSync.

#### **Using the List ID**:

1. Go to your Trakt list in your browser.
2. Look for the blue "Share" button, located in the list.
3. ![trakt-help](https://share.woahlab.com/-Nx5VJnbUEY)
4. Hover over it, and it should say "**Copy Link**".
5. The copied link will be in the format: `https://trakt.tv/lists/12345678` or `https://trakt.tv/users/username/lists/12345678`.
6. The list ID is the number at the end. In this example, it would be `12345678`.

### Adding Multiple List IDs

When inputting list IDs or URLs, you can add multiple lists by separating them with commas. For example:

- IMDb: `ls012345678,12345678,https://www.imdb.com/chart/top/,ur987654321,https://trakt.tv/lists/87654321`

This allows you to sync multiple lists at once, whether they are custom lists, charts, or watchlists.

## 📋 Notes

- **Security Best Practices:** Please read scripts you find online before running them.
- **API Credentials:** Always keep your API credentials secure.
- **Rate Limiting:** Be mindful of Overseerr's rate limiting policies during imports.
- **Permissions:** Only import and manage media you have the rights to handle.

## 💰 Donations

If you find ListSync useful and would like to support its development, consider making a donation:

- BTC (Bitcoin): `bc1qxjpfszwvy3ty33weu6tjkr394uq30jwkysp4x0`
- ETH (Ethereum): `0xAF3ADE79B7304784049D200ea50352D1C717d7f2`

Thank you for your support!

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

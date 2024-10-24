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


Welcome to the **ListSync Tool**! 🎉

This powerful tool automates the import of your carefully curated IMDB and Trakt lists into Overseerr, transforming movie and TV show management into a breeze. Whether you're a cinephile, a librarian for multiple collections, or someone enchanted by the magic of automation, this tool is here to simplify your experience.

## 📜 Table of Contents

1. [Demo](#-demo)
2. [Key Features](#-key-features)
3. [Compatibility](#-compatibility)
4. [Getting Started](#-getting-started)
   - [Installation: Docker (Recommended)](#installation-docker-recommended)
   - [Standard Python Environment](#standard-python-environment)
   - [Poetry](#poetry)
   - [Configuration](#configuration)
5. [Obtaining List IDs](#-obtaining-list-ids)
6. [How it Works](#-how-it-works)
7. [Troubleshooting](#-troubleshooting)
8. [Roadmap](#-roadmap)
9. [Notes](#-notes)
10. [Contact](#-contact)
11. [Contributing](#-contributing)
12. [License](#-license)
13. [Fun Zone: Get to Know Your Tool!](#-fun-zone-get-to-know-your-tool)
14. [Legal Disclaimer](#-legal-disclaimer)

## 🎬 Demo

![Bot In Action](https://share.woahlab.com/-BZtwSD96LN)

---

### 🔑 Key Features

| Feature                                      | Status |
| -------------------------------------------- | ------ |
| **List Management**                          |        |
| - Simultaneous List Import                   | ✅     |
| - Support for IMDB & Trakt Lists             | ✅     |
| - Multi-page Trakt List Fetching             | ✅     |
| - List Management Menu                       | ✅     |
| **Media Processing**                         |        |
| - Fetch & Import Movies & TV Shows           | ✅     |
| - Identify Media Already Requested           | ✅     |
| - Identify Media Already Available           | ✅     |
| **Performance**                              |        |
| - Thread Pool Executor for Concurrent Processing | ✅     |
| **Configuration & Security**                 |        |
| - Encrypted Configuration Storage            | ✅     |
| - Configurable Sync Interval                 | ✅     |
| **User Experience**                          |        |
| - Real-time Detailed Logging                 | ✅     |
| - Graceful Exit During Sleep                 | ✅     |
| - Dry Run Mode                               | ✅     |

---

## 📊 Compatibility

| Application | Status | Notes |
|:-----------:|:------:|:------|
| ![Overseerr](https://img.shields.io/badge/Overseerr-1.33.2+-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Full functionality with Overseerr |
| ![Jellyseerr](https://img.shields.io/badge/Jellyseerr-1.9.2+-purple?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Full functionality with Jellyseerr |
| ![Radarr](https://img.shields.io/badge/Radarr-5.11.0+-orange?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Started with supporting movies |
| ![Sonarr](https://img.shields.io/badge/Sonarr-4.0.9+-5cad7b?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABB0lEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Now also supports TV shows |

### Supported List Services

| Service | Status | Notes |
|:-------:|:------:|:------|
| ![IMDB](https://img.shields.io/badge/IMDB-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Currently supported |
| ![Trakt](https://img.shields.io/badge/Trakt-green?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ✅ Supported | Currently supported |

### Future List Services

| Service | Status | Notes |
|:-------:|:------:|:------|
| ![Letterboxd](https://img.shields.io/badge/Letterboxd-red?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABKElEQVQ4jZXTMUoDQRQG4C+7YmFhYSHYWFgIHkAQPICFhYcQBEEQxGNYWHgIC0H0BsELWFhYWAQLC2GzxSzsLrOz2f0hMDDvzXvfzLz3ZkopKKMxxrjHJc7wjjd0UgpfZRYVgbM4P2AevZzEHlZwiU5KYa8QmMUNtnCMh5TCqCR0jgF6eEQfq1jHFfbRxHFKYVQQWMQIZxjGehObeEUH7ZTCJCcYx2Ub99jGEEtYwDnWsIk2LlIK/ZzALK7RwlKsPWMppfAc/m+0UwrTnKCBHt7iZnlp5/GCVkrhKyd4wg5WYv6NTkrhNSdoRd0b2Cg0z0dOcIj9uHnePG/+t/k3wR/kyUNUdQE+UAAAAABJRU5ErkJgg==) | ❌ Not Yet | Future support planned |

---

## 🚀 Getting Started

### Installation Methods

| Installation Method | Command | Notes |
|:-------------------:|:-------:|:------|
| ![Docker](https://img.shields.io/badge/Docker-ready-blue?style=for-the-badge&logo=docker) | `sudo docker pull ghcr.io/woahai321/list-sync:main && sudo docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main` | Easy containerized deployment |
| ![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python) | `pip install -r requirements.txt && python add.py` | Requires Python 3.7+ |
| ![Poetry](https://img.shields.io/badge/Poetry-ready-blue?style=for-the-badge&logo=poetry) | `poetry install && poetry run python add.py` | Simplifies dependency management |


### Docker (Recommended)

To ensure the tool runs consistently across different environments, use Docker.

1. **Install Docker**:

   Ensure Docker is installed on your system. If it's not, follow the [installation guide](https://docs.docker.com/get-docker/) for your operating system.

2. **Create a working directory**:

   Make a folder to house the application's log files (e.g. list-sync)

3. **Pull and Run the Docker Image**:

   Navigate to your directory and use the following one-liner to pull and run the Docker image:

   ```sh
   sudo docker pull ghcr.io/woahai321/list-sync:main && sudo docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main
   ```

4. **Use this command for subsequent runs**:

   Use the following command to run the Docker image:

   ```sh
   sudo docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main
   ```

### Standard Python Environment

If you prefer running the tool in a standard Python environment, follow these steps:

1. **Clone the Repository and Navigate to the Directory**:

   ```sh
   git clone https://github.com/woahai321/list-sync.git
   cd list-sync
   ```

2. **Install Dependencies**:

   Make sure you have Python 3.9 or higher installed, then install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the Script**:

   ```sh
   python add.py
   ```

### Poetry

Poetry offers several advantages over traditional Python dependency management methods:

- **Ease of Use:** Simplifies the installation process with a single command and manages virtual environments automatically.
- **Version Control:** Tracks exact package versions, making it easier to reproduce environments and avoid version drift.
- **Security:** Integrates with security tools to scan for vulnerabilities in dependencies.
- **Cross-Platform Compatibility:** Ensures consistent behaviour across different operating systems.

#### Installation and Usage with Poetry

1. **Install Poetry**:

   ```sh
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone the Repository and Navigate to the Directory**:

   ```sh
   git clone https://github.com/woahai321/list-sync.git
   cd list-sync
   ```

3. **Install Dependencies**:

   Make sure you have Python 3.9 or higher installed, then install the required dependencies:

   ```sh
   poetry install
   ```

4. **Run the Script**:

   ```sh
   poetry run python add.py
   ```

Alternatively, use [devcontainer](.devcontainer/devcontainer.json) to bootstrap a pre-built dev environment: [DevContainer documentation](https://containers.dev/)

### Configuration

1. **Run the Script and Fill in the Required Details When Prompted**:

   - **Overseerr URL**: Your Overseerr instance's base URL.
   - **API Key**: The API key from your Overseerr account.
   - **IMDB List ID(s)**: The ID(s) of the IMDB list(s) you want to import.
   - **Trakt List ID(s)**: The ID(s) of the Trakt list(s) you want to import.

2. **Saving Configuration**:
   - The script will prompt you to enter a password to encrypt your configuration.
   - This encrypted configuration will be saved and reused for future imports.

---

## 🔍 Obtaining List IDs

### IMDB List ID

To obtain an IMDB list ID:

1. Navigate to your IMDB list.
2. Look at the URL. It should be in the format: `https://www.imdb.com/list/ls012345678/`
3. The list ID is the `ls` number. In this example, it would be `ls012345678`.

### Trakt List ID

To obtain a Trakt list ID:

1. Go to your Trakt list.
2. Look for the blue "Share" button, located in the list
3. ![trakt-help](https://share.woahlab.com/-Nx5VJnbUEY)
4. Hover over it, it should say "**Copy Link**".
5. The copied link will be in the format: `https://trakt.tv/lists/12345678`
6. The list ID is the number at the end. In this example, it would be `12345678`.

### Adding Multiple List IDs

When inputting list IDs, you can add multiple IDs by separating them with commas.
---

## 🔎 How it Works

The ListSync Tool is a Python-based application that leverages several libraries and the [Overseerr API](https://api-docs.overseerr.dev/#/) to seamlessly integrate your IMDB and Trakt lists with Overseerr. Here's a detailed breakdown of its functionality:

1. **Authentication and Security:**
   - Credentials are encrypted using the `cryptography` library's Fernet symmetric encryption.
   - Encrypted data is stored locally, ensuring your sensitive information remains protected.

2. **List Fetching and Parsing:**
   - For IMDB lists:
     - Utilizes `requests` to fetch the HTML content of the IMDB list.
     - Employs `BeautifulSoup` to parse the HTML and extract structured data.
   - For Trakt lists:
     - Nearly the same process 1:1
     - Parses the HTML response to extract media information.

3. **Overseerr Integration:**
   - Interacts with the Overseerr API using the `requests` library.
   - Implements minimal rate limiting to prevent overwhelming the Overseerr server and webhooks.
   - Performs media searches, status checks, and request submissions via API endpoints.

4. **Intelligent Processing:**
   - Differentiates between movies and TV shows for appropriate handling.
   - For TV shows, it determines the number of seasons and requests all available seasons.
   - Checks if media is already available or requested before submitting new requests.

5. **Error Handling and Logging:**
   - Implements comprehensive error handling for network issues, API errors, and parsing problems.
   - Utilises Python's `logging` module to maintain detailed logs for troubleshooting.
   - Provides real-time status updates in the console using the `colorama` and `halo` libraries.

6. **Periodic Syncing:**
   - Offers the option to set up recurring syncs at user-defined intervals.
   - Implements a sleep mechanism that can be interrupted for on-demand actions.

7. **User Interface:**
   - Presents a user-friendly command-line interface with color-coded outputs.
   - Displays ASCII art and banners for an engaging user experience.
   - Provides summary statistics after each sync operation.

---

## 🛠 Troubleshooting

### Common Issues and Solutions

1. **Invalid API Credentials**
   - **Symptom:** Error messages related to API authentication or 401 Unauthorised responses.
   - **Solution:** 
     - Double-check your Overseerr URL and API key in the Overseerr settings.
     - Ensure there are no trailing spaces in the URL or API key.
     - Try regenerating your API key in Overseerr and updating the script's configuration.

2. **Script Crashes or Unexpected Behavior**
   - **Symptom:** Script terminates unexpectedly or produces unexpected results.
   - **Solution:** 
     - Check the `overseerr_sync.log` file in the `./data` directory for detailed error messages.
     - Look for Python tracebacks which can pinpoint the exact line causing the issue.
     - Ensure all required Python libraries are installed and up-to-date.
     - Verify that your Python version meets the minimum requirements (Python 3.7+).

3. **Failed to Fetch List**
   - **Symptom:** Error messages indicating failure to retrieve IMDB or Trakt lists.
   - **Solution:** 
     - Verify that the list ID is correct and the list is publicly accessible.
     - Check your internet connection and firewall settings.
     - For IMDB lists, ensure the list URL follows the format: `https://www.imdb.com/list/ls012345678/`
     - For Trakt lists, confirm the list URL is in the format when copied: `https://trakt.tv/lists/1234567`

4. **Decryption Error**
   - **Symptom:** Unable to decrypt configuration or "Incorrect password" error.
   - **Solution:** 
     - Ensure you're entering the correct password used during initial setup.
     - If you've forgotten the password, delete the `config.enc` file in the `./data` directory and run the script again to reconfigure.
     - Check file permissions to ensure the script has read/write access to the `./data` directory.

5. **Rate Limiting Issues**
   - **Symptom:** Frequent "Too Many Requests" errors or slow processing.
   - **Solution:** 
     - Increase the delay between requests by adjusting the `time.sleep()` value in the script.
     - Consider reducing the size of your lists or splitting them into smaller chunks.

6. **Media Not Found in Overseerr**
   - **Symptom:** Many items reported as "Not found" during processing.
   - **Solution:** 
     - Verify that Overseerr is properly connected to your media sources (Radarr/Sonarr).
     - Check if the titles in your lists match exactly with how they appear in Overseerr's search.
     - For TV shows, try using the original title rather than localised versions.

If you encounter persistent issues not covered here, please remeber this is in beta development and you will find bugs.

---

## 🛤️ Roadmap

### Small Tasks

- [x] **Enhanced Error Messages:** Improve error descriptions for easier troubleshooting.
- [x] **Advanced Error Handling:** Improved error messages for clearer troubleshooting.
- [x] **Secure User Profiles:** Ability to save and load Overseerr details from an encrypted configuration file.
- [x] **Real-time Progress Updates:** Real-time progress updates for importing movies and TV shows.

### Medium Tasks

- [x] **Integration with Other Services:** Trakt
- [x] **Interruptible Sleep Mode:** Functionality for interrupting sleep mode for on-demand sync or clean exit.
- [x] **Configuration Management:** Save and reuse configuration setups.
- [x] **Batch Processing:** Enable batch processing for multiple lists simultaneously.
- [x] **Support for TV Shows:** Extend functionality to import TV shows from IMDB and Trakt lists.
- [x] **Database Integration:** Implement a real database to track sync history and metrics, not just a file.
- [ ] **Integration with Other Services:** Letterboxd, etc.
- [ ] **Customisation Options:** Allow users to fully customise the UI and behaviour of the tool.

### Big Tasks

- [x] **Automated Syncing:** Schedule automatic syncing between IMDB/Trakt and Overseerr.
- [x] **Movie Status Identification:** Identify movies already available, already requested, or to be requested.
- [x] **TV Series Status Identification:** Identify TV series already available, already requested, or to be requested.
- [x] **Encrypted Configuration Storage:** Implemented encrypted storage for Overseerr API credentials.
- [ ] **External Notifications:** Add webhook notifications for sync status and errors.
- [ ] **Web Dashboard:** Create a web-based interface for more user-friendly interaction.
- [ ] **Advanced Analytics Dashboard:** Provide detailed analytics and insights into the sync operations.
- [ ] **Machine Learning Suggestions:** Use ML to suggest movies and TV shows based on user preferences and history.

---

## 📋 Notes

- **Security Best Practices:** Please read scripts you find online before running them.
- **Security Best Practices (Cont.):** Always keep your API credentials secure.
- **Rate Limiting Awareness:** Be mindful of Overseerr's rate limiting policies during imports.
- **Permission Compliance:** Only import and manage media you have the rights to handle.

---

## 📞 Contact

Need help or have questions? Don't hesitate to raise an issue on this repo; we're here to help!

---

## 💰 Donations

If you find our work useful and would like to support us, feel free to make a donation using the addresses below:

- BTC (Bitcoin): `bc1qxjpfszwvy3ty33weu6tjkr394uq30jwkysp4x0`
- ETH (Ethereum): `0xAF3ADE79B7304784049D200ea50352D1C717d7f2`

Thank you for your support!

---

## 🤝 Contributing

We appreciate your contributions! Here's how to get involved:

1. **Fork the repository** on GitHub.
2. **Create a new branch** for your feature or bug fix.
3. **Make your changes** and commit them with descriptive messages.
4. **Submit a pull request** for review.

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/license/mit). Review the LICENSE file for more details.

---

# 🎉 Fun Zone: Get to Know Your Tool!

Buckle up for some fun insights and interesting facts! Your ListSync Tool is more than just software; it's your new best friend in movie and TV show management.


## 🤓 Fun Facts

- **Cinema History:** The first drive-in theater opened in 1933 in New Jersey. 🚗🎥 [Source](https://en.m.wikipedia.org/wiki/File:First_drive-in_theater_Camden_NJ_1933.jpg#:~:text=in%20Pennsauken%2C%20near%20Camden%2C%20New,Adolphe%20Menjou%27s%20Wife%20Beware.)
- **Legendary Cameo:** Alfred Hitchcock made cameo appearances in 39 of his 52 surviving major films! 🎭 [Source](https://hitchcock.fandom.com/wiki/Alfred_Hitchcock_cameo_appearances#:~:text=English%20film%20director%20Alfred%20Hitchcock,trying%20to%20spot%20his%20cameos.)
- **Oscar Records:** Walt Disney holds the record for the most Oscars with 22 wins and 59 nominations. 🏆 [Source](https://www.emmys.com/bios/walt-disney#:~:text=As%20a%20film%20producer%2C%20Disney,Emmy%20Award%2C%20among%20other%20honors.)
- **Expensive Set:** "Pirates of the Caribbean: On Stranger Tides" is one of the most expensive movies ever made, with a budget of $379 million. 🏴‍☠️ [Source](https://en.wikipedia.org/wiki/Pirates_of_the_Caribbean:_On_Stranger_Tides#:~:text=Filming%20employed%203D%20cameras%20similar,the%20time%20of%20its%20release.)
- **Film Length:** The longest movie ever made is the experimental film "Modern Times Forever," which runs for 240 hours (10 days). 🎬 [Source](https://www.forbesindia.com/article/explainers/longest-films-by-running-time/93944/1#:~:text=Directed%20by%20the%20Finnish%20art,the%20building%27s%20transformation%20over%20time.)
- **Box Office King:** "Avengers: Endgame" surpassed "Avatar" to become the highest-grossing film of all time. 💰 [Source](https://variety.com/2021/film/news/avatar-avengers-endgame-highest-grossing-movie-all-time-1234929216/#:~:text=“Avengers%3A%20Endgame”%20eclipsed%20that,to%20a%20historic%20%242.7926%20billion.)

---

## 🛡️ Legal Disclaimer

Using the **ListSync Tool** responsibly and in accordance with Overseerr's, IMDB's & Trakt's Terms of Service (ToS) and policies is crucial! Here are some key points:

1. **Compliance with Overseerr and IMDB:**

   - Users must adhere to the ToS of all third parties in use.

2. **No Spamming or Abuse:**

   - This tool should not be used for spam or unauthorised import activities. Respect the guidelines and policies of the platforms.

3. **Managing Rate Limits:**

   - Use the tool thoughtfully to avoid hitting rate limits set by Overseerr. Excessive usage can lead to rate limiting or bans.

4. **User Consent:**

   - Ensure you have the necessary permissions to import and manage media from IMDB lists.

5. **Security:**

   - Protect your API credentials and never share them publicly.

6. **Responsibility:**
   - Users are responsible for their actions while using this tool. The creators of the **ListSync Tool** are not liable for any misuse or legal consequences arising from its use.

# 🎬 ListSync

![ListSync Logo](https://share.woahlab.com/-Tdgu2viusH)
[![Website](https://img.shields.io/website?label=soluify.com&style=plastic&url=https%3A%2F%2Fsoluify.com)](https://soluify.com/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?style=plastic&logo=linkedin)](https://www.linkedin.com/company/soluify)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen)

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

![Bot In Action](https://share.woahlab.com/-ofxGvTz7Wb)

---

## 🔑 Key Features

| Feature                                      | Status |
| -------------------------------------------- | ------ |
| Multiple List Import                         | ✅     |
| Fetch and Import Movies & TV Shows           | ✅     |
| Support for IMDB and Trakt Lists             | ✅     |
| Identify Movies & TV Shows Already Requested | ✅     |
| Identify Movies & TV Shows Already Available | ✅     |
| Real-time Detailed Logging                   | ✅     |
| Encrypted Configuration Storage              | ✅     |
| Configurable Sync Interval                   | ✅     |
| On-demand Sync During Sleep                  | ✅     |
| Graceful Exit During Sleep                   | ✅     |

---

## 📊 Compatibility

This tool is compatible with the following:

| Application                                                    | Status       | Notes                             |
| -------------------------------------------------------------- | ------------ | --------------------------------- |
| ![Overseerr](https://img.shields.io/badge/-Overseerr-blue)     | ✅ Supported | Full functionality with Overseerr |
| ![Jellyseerr](https://img.shields.io/badge/-Jellyseerr-purple) | ✅ Supported | Compatible with Jellyseerr        |
| ![Radarr](https://img.shields.io/badge/-Radarr-orange)         | ✅ Supported | Currently supports Radarr         |
| ![Sonarr](https://img.shields.io/badge/-Sonarr-gray)           | ✅ Supported | Now supports TV series            |

### Supported List Services

| Service                                             | Status       | Notes               |
| --------------------------------------------------- | ------------ | ------------------- |
| ![IMDB](https://img.shields.io/badge/-IMDB-green)   | ✅ Supported | Currently supported |
| ![Trakt](https://img.shields.io/badge/-Trakt-green) | ✅ Supported | Currently supported |

### Future List Services

| Service                                                     | Status       | Notes                  |
| ----------------------------------------------------------- | ------------ | ---------------------- |
| ![Letterboxd](https://img.shields.io/badge/-Letterboxd-red) | ❌ Not Yet   | Future support planned |

---

## 🚀 Getting Started

### Installation: Docker (Recommended)

To ensure the tool runs consistently across different environments, use Docker.

1. **Install Docker**:

   Ensure Docker is installed on your system. If it's not, follow the [installation guide](https://docs.docker.com/get-docker/) for your operating system.

2. **Create a working directory**:

   Make a folder to house the application's log files (e.g. list-sync)

3. **Pull and Run the Docker Image**:

   Use the following one-liner to pull and run the Docker image:

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
2. Look for the blue "Share" button, located to the right of the title and left of the "Copy" button.
3. Hover over it, it should say "Copy Link".
4. The copied link will be in the format: `https://trakt.tv/lists/12345678`
5. The list ID is the number at the end. In this example, it would be `12345678`.

### Adding Multiple List IDs

When inputting list IDs, you can add multiple IDs by separating them with commas. However, please note:

- You can add multiple IMDB IDs together, and multiple Trakt IDs together.
- You cannot mix IMDB and Trakt IDs in the same input.

Example:
- IMDB: `ls012345678,ls987654321`
- Trakt: `20492796,30492797`

---

## 🔎 How it Works

The ListSync Tool utilises a mix of Python and powerful libraries like `requests`, `BeautifulSoup`, and the [Overseerr API](https://api-docs.overseerr.dev/#/) to find and request missing movies and TV shows.

Here's a brief breakdown:

1. **Authentication:** Input your Overseerr URL and API key to securely interact with your movie and TV show library.
2. **List Fetching:** Fetch and parse movies and TV shows from your specified IMDB and Trakt list IDs.
3. **Processing:** The tool processes each movie and TV show, importing it into Overseerr, while handling any errors that come up.
4. **Status Updates:** Receive real-time updates on the status of each movie and TV show (e.g., already available, requested, not found).
5. **Encryption:** Securely encrypt your configuration data to ensure your credentials are protected.

---

## 🛠 Troubleshooting

### Common Issues

1. **Invalid API Credentials**

   - **Solution:** Ensure your API key is correctly entered and matches Overseerr's credentials.

2. **Unexpected Script Behaviour**

   - **Solution:** Check the `overseerr_sync.log` file for detailed error messages and resolve the issue based on these logs.

3. **Failed to Fetch List**

   - **Solution:** Ensure the IMDB or Trakt list ID is correct and the list is publicly accessible.

4. **Decryption Error**
   - **Solution:** Ensure you enter the correct password for decrypting the configuration. If the password is lost, delete the `config.enc` file and reconfigure.

---

## 🛤️ Roadmap

### Small Tasks

- [x] **Enhanced Error Messages:** Improve error descriptions for easier troubleshooting.
- [x] **Advanced Error Handling:** Improved error messages for clearer troubleshooting.
- [x] **Secure User Profiles:** Ability to save and load Overseerr details from an encrypted configuration file.
- [x] **Real-time Progress Updates:** Real-time progress updates for importing movies and TV shows.
- [x] **Integration with Other Services:** Trakt
- [ ] **Integration with Other Services:** Letterboxd, etc.

### Medium Tasks

- [x] **Interruptible Sleep Mode:** Functionality for interrupting sleep mode for on-demand sync or clean exit.
- [x] **Configuration Management:** Save and reuse configuration setups.
- [x] **Batch Processing:** Enable batch processing for multiple lists simultaneously.
- [x] **Support for TV Shows:** Extend functionality to import TV shows from IMDB and Trakt lists.
- [ ] **Customisation Options:** Allow users to fully customise the UI and behaviour of the tool.
- [ ] **Database Integration:** Implement a real database to track sync history and metrics, not just a file.

### Big Tasks

- [x] **Automated Syncing:** Schedule automatic syncing between IMDB/Trakt and Overseerr.
- [x] **Movie Status Identification:** Identify movies already available, already requested, or to be requested.
- [x] **TV Series Status Identification:** Identify TV series already available, already requested, or to be requested.
- [x] **Dynamic Status Updates:** Combined processing message and status update in one line with dynamic colour changes.
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

- **Cinema History:** The first drive-in theatre opened in 1933 in New Jersey. 🚗🎥 [Source](https://en.m.wikipedia.org/wiki/File:First_drive-in_theater_Camden_NJ_1933.jpg#:~:text=in%20Pennsauken%2C%20near%20Camden%2C%20New,Adolphe%20Menjou%27s%20Wife%20Beware.)
- **Legendary Cameo:** Alfred Hitchcock made cameo appearances in 39 of his 52 surviving major films! 🎭 [Source](https://hitchcock.fandom.com/wiki/Alfred_Hitchcock_cameo_appearances#:~:text=English%20film%20director%20Alfred%20Hitchcock,trying%20to%20spot%20his%20cameos.)
- **Oscar Records:** Walt Disney holds the record for the most Oscars with 22 wins and 59 nominations. 🏆 [Source](https://www.emmys.com/bios/walt-disney#:~:text=As%20a%20film%20producer%2C%20Disney,Emmy%20Award%2C%20among%20other%20honors.)
- **Expensive Set:** "Pirates of the Caribbean: On Stranger Tides" is one of the most expensive movies ever made, with a budget of $379 million. 🏴‍☠️ [Source](https://en.wikipedia.org/wiki/Pirates_of_the_Caribbean:_On_Stranger_Tides#:~:text=Filming%20employed%203D%20cameras%20similar,the%20time%20of%20its%20release.)

## 🤓 Fun Facts

- **Cinema History:** The first drive-in theater opened in 1933 in New Jersey. 🚗🎥 [Source](https://en.m.wikipedia.org/wiki/File:First_drive-in_theater_Camden_NJ_1933.jpg#:~:text=in%20Pennsauken%2C%20near%20Camden%2C%20New,Adolphe%20Menjou%27s%20Wife%20Beware.)
- **Legendary Cameo:** Alfred Hitchcock made cameo appearances in 39 of his 52 surviving major films! 🎭 [Source](https://hitchcock.fandom.com/wiki/Alfred_Hitchcock_cameo_appearances#:~:text=English%20film%20director%20Alfred%20Hitchcock,trying%20to%20spot%20his%20cameos.)
- **Oscar Records:** Walt Disney holds the record for the most Oscars with 22 wins and 59 nominations. 🏆 [Source](https://www.emmys.com/bios/walt-disney#:~:text=As%20a%20film%20producer%2C%20Disney,Emmy%20Award%2C%20among%20other%20honors.)
- **Expensive Set:** "Pirates of the Caribbean: On Stranger Tides" is one of the most expensive movies ever made, with a budget of $379 million. 🏴‍☠️ [Source](https://en.wikipedia.org/wiki/Pirates_of_the_Caribbean:_On_Stranger_Tides#:~:text=Filming%20employed%203D%20cameras%20similar,the%20time%20of%20its%20release.)
- **Film Length:** The longest movie ever made is the experimental film "Modern Times Forever," which runs for 240 hours (10 days). 🎬 [Source](https://www.forbesindia.com/article/explainers/longest-films-by-running-time/93944/1#:~:text=Directed%20by%20the%20Finnish%20art,the%20building%27s%20transformation%20over%20time.)
- **Box Office King:** "Avengers: Endgame" surpassed "Avatar" to become the highest-grossing film of all time. 💰 [Source](https://variety.com/2021/film/news/avatar-avengers-endgame-highest-grossing-movie-all-time-1234929216/#:~:text=“Avengers%3A%20Endgame”%20eclipsed%20that,to%20a%20historic%20%242.7926%20billion.)

---

## 🛡️ Legal Disclaimer

Using the **ListSync Tool** responsibly and in accordance with Overseerr's and IMDB's Terms of Service (ToS) and policies is crucial! Here are some key points:

1. **Compliance with Overseerr and IMDB:**

   - Users must adhere to the ToS of both Overseerr and IMDB. Review IMDB's [Terms of Service](https://www.imdb.com/conditions) to ensure compliance.

2. **No Spamming or Abuse:**

   - This tool should not be used for spam or unauthorized import activities. Respect the guidelines and policies of the platforms.

3. **Managing Rate Limits:**

   - Use the tool thoughtfully to avoid hitting rate limits set by Overseerr. Excessive usage can lead to rate limiting or bans.

4. **User Consent:**

   - Ensure you have the necessary permissions to import and manage media from IMDB lists.

5. **Security:**

   - Protect your API credentials and never share them publicly.

6. **Responsibility:**
   - Users are responsible for their actions while using this tool. The creators of the **ListSync Tool** are not liable for any misuse or legal consequences arising from its use.

# 🎬 IMDB to Overseerr Sync Tool

![IMDB to Overseerr Logo](https://share.woahlab.com/-G7FV7AkDqV)
[![Website](https://img.shields.io/website?label=soluify.com&style=plastic&url=https%3A%2F%2Fsoluify.com)](https://soluify.com/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?style=plastic&logo=linkedin)](https://www.linkedin.com/company/soluify)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen)

Welcome to the **IMDB to Overseerr Sync Tool**! 🎉 This amazing tool automates importing your carefully curated IMDB lists into Overseerr, transforming movie management into a breeze. Whether you're a movie buff, a librarian for multiple collections, or someone enchanted by the magic of automation, this tool is here to simplify your experience.

## 📜 Table of Contents

1. [Demo](#-demo)
2. [Features](#-features)
3. [How it Works](#-how-it-works)
4. [Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation Steps](#installation-steps)
    - [Configuration](#configuration)
5. [Troubleshooting](#-troubleshooting)
6. [Roadmap](#-roadmap)
7. [Notes](#-notes)
8. [Contact](#-contact)
9. [Contributing](#-contributing)
10. [License](#-license)
11. [Fun Zone: Get to Know Your Tool!](#-fun-zone-get-to-know-your-tool)

## 🎬 Demo

![Bot In Action](https://share.woahlab.com/-J7uDtsPvq3)

---

## 🌟 Features

- **Automatic IMDB Import**: Easily fetch and import movies from IMDB lists into Overseerr with a few clicks.
- **Real-time Progress Updates**: Get instant feedback and updates on the status of your movie requests.
- **Refined and Colorful UI**: Enjoy a sleek interface with eye-catching elements and helpful messages.
- **Advanced Error Handling**: Comprehensive logging and error messages to help you troubleshoot anything.
- **One-time Configuration**: Save and reuse configuration profiles, simplifying future imports.
- **Seamless Exit**: Gracefully stop the import process without losing your place.

---

## 🔎 How it Works

The IMDB to Overseerr Sync Tool utilizes a mix of Python and powerful libraries like `requests`, `BeautifulSoup`, and `Halo`. Here’s a brief breakdown:

1. **Authentication**: Input your Overseerr URL and API key to securely access your movie library.
2. **IMDB List Fetching**: Fetch and parse movies from your specified IMDB list ID.
3. **Configuration Management**: Tailor the tool to your preferences, and save these settings for future use.
4. **Processing**: The tool processes each movie, importing it into Overseerr, while handling any errors that come up.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.7 or higher**
- Basic command line knowledge
- Compatible with most operating systems, best on Ubuntu

### Installation Steps

Start up your terminal and follow these steps:

```bash
# Clone the repository
git clone https://github.com/woahai321/imdb-to-overseerr.git
cd imdb-to-overseerr

# Install dependencies
pip install -r requirements.txt

# Run the script
python add.py
```

### Configuration

1. **Run the script and fill in the required details when prompted:**
    - **Overseerr URL**: Your Overseerr instance's base URL.
    - **API Key**: The API key from your Overseerr account.
    - **IMDB List ID**: The ID of the IMDB list you want to import.

---

## 🛠 Troubleshooting

### Common Issues

1. **Invalid API Credentials**
   - **Solution:** Ensure your API key is correctly entered and matches Overseerr's credentials.

2. **Unexpected Script Behavior**
   - **Solution:** Check the `add.log` file for detailed error messages and resolve the issue based on these logs.

---

## 🛤️ Roadmap

### Next Steps
1. [x] **Enhanced Error Messages**: Improve error descriptions for easier troubleshooting.
2. [x] **User Profiles**: Ability to save and load Overseerr details from a configuration file.
3. [ ] **Support for TV Shows**: Extend functionality to import TV shows from IMDB lists.

### Future Enhancements
4. [ ] **Web Dashboard**: Create a web-based interface for more user-friendly interaction.
5. [ ] **Batch Processing**: Enable batch processing for multiple IMDB lists simultaneously.

### Long-term Goals
6. [ ] **Automated Syncing**: Schedule automatic syncing between IMDB and Overseerr.
7. [ ] **Customization Options**: Allow users to fully customize the UI and behavior of the tool.

---

## 📋 Notes

- **Security Best Practices**: Please read scripts you find online before running them.
- **Security Best Practices Cont.**: Always keep your API credentials secure.
- **Rate Limiting Awareness**: Be mindful of Overseerr's rate limiting policies during imports.
- **Permission Compliance**: Only import and manage media you have the rights to handle.

---

## 📞 Contact

Need help or have questions? Don't hesitate to raise an issue on this repo; we're here to help!

---

## 🤝 Contributing

We appreciate your contributions! Here’s how to get involved:

1. **Fork the repository** on GitHub.
2. **Create a new branch** for your feature or bug fix.
3. **Make your changes** and commit them with descriptive messages.
4. **Submit a pull request** for review.

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/license/mit). Review the LICENSE file for more details.

---

# 🎉 Fun Zone: Get to Know Your Tool!

Buckle up for some fun insights and interesting facts! Your IMDB to Overseerr Sync Tool is more than just software; it’s your new best friend in movie management.

## 🤓 Fun Facts

- **Cinema History**: The first drive-in theater opened in 1933 in New Jersey. 🚗🎥 [Source](https://en.m.wikipedia.org/wiki/File:First_drive-in_theater_Camden_NJ_1933.jpg#:~:text=in%20Pennsauken%2C%20near%20Camden%2C%20New,Adolphe%20Menjou%27s%20Wife%20Beware.)
- **Legendary Cameo**: Alfred Hitchcock made cameo appearances in 39 of his 52 surviving major films! 🎭 [Source](https://hitchcock.fandom.com/wiki/Alfred_Hitchcock_cameo_appearances#:~:text=English%20film%20director%20Alfred%20Hitchcock,trying%20to%20spot%20his%20cameos.)
- **Oscar Records**: Walt Disney holds the record for the most Oscars with 22 wins and 59 nominations. 🏆 [Source](https://www.emmys.com/bios/walt-disney#:~:text=As%20a%20film%20producer%2C%20Disney,Emmy%20Award%2C%20among%20other%20honors.)
- **Expensive Set**: "Pirates of the Caribbean: On Stranger Tides" is one of the most expensive movies ever made, with a budget of $379 million. 🏴‍☠️ [Source](https://en.wikipedia.org/wiki/Pirates_of_the_Caribbean:_On_Stranger_Tides#:~:text=Filming%20employed%203D%20cameras%20similar,the%20time%20of%20its%20release.)
- **Film Length**: The longest movie ever made is the experimental film "Modern Times Forever," which runs for 240 hours (10 days). 🎬 [Source](https://www.forbesindia.com/article/explainers/longest-films-by-running-time/93944/1#:~:text=Directed%20by%20the%20Finnish%20art,the%20building%27s%20transformation%20over%20time.)
- **Box Office King**: "Avengers: Endgame" surpassed "Avatar" to become the highest-grossing film of all time. 💰 [Source](https://variety.com/2021/film/news/avatar-avengers-endgame-highest-grossing-movie-all-time-1234929216/#:~:text=“Avengers%3A%20Endgame”%20eclipsed%20that,to%20a%20historic%20%242.7926%20billion.)

## 🏆 Tool Achievements

Our tool isn’t just functional; it’s a superstar! Here are some of the milestones it has achieved:

- **Bulk Import Champ**: Imported over 1,000  movies from one list  without a hitch.
- **Rapid Processor**: Handles large IMDB lists with speed and accuracy.
- **User-Friendly Interface**: Boasts an interface that users love for its simplicity and intuitiveness.

---

## 🛡️ Legal Disclaimer

Using the **IMDB to Overseerr Sync Tool** responsibly and in accordance with Overseerr's and IMDB's Terms of Service (ToS) and policies is crucial. Here are some key points:

1. **Compliance with Overseerr and IMDB**:
    - Users must adhere to the ToS of both Overseerr and IMDB. Review IMDB's [Terms of Service](https://www.imdb.com/conditions) to ensure compliance.

2. **No Spamming or Abuse**:
    - This tool should not be used for spam or unauthorized import activities. Respect the guidelines and policies of the platforms.

3. **Managing Rate Limits**:
    - Use the tool thoughtfully to avoid hitting rate limits set by Overseerr. Excessive usage can lead to rate limiting or bans.

4. **User Consent**:
    - Ensure you have the necessary permissions to import and manage media from IMDB lists.

5. **Security**:
    - Protect your API credentials and never share them publicly.

6. **Responsibility**:
    - Users are responsible for their actions while using this tool. The creators of the **IMDB to Overseerr Sync Tool** are not liable for any misuse or legal consequences arising from its use.

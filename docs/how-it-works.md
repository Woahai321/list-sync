# How ListSync Works

ListSync is a powerful tool that bridges your IMDB and Trakt lists with Overseerr, automating the process of importing and managing your media requests. Here's a detailed breakdown of its functionality:

## 1. Authentication and Security

- ListSync uses the `cryptography` library's Fernet symmetric encryption to secure your credentials.
- Your encrypted data is stored locally, ensuring that your sensitive information remains protected.

## 2. List Fetching and Parsing

### IMDB Lists

- The tool uses the `requests` library to fetch the HTML content of your IMDB list.
- It then employs `BeautifulSoup` to parse the HTML and extract structured data about movies and TV shows.

### Trakt Lists

- A similar process is used for Trakt lists.
- The HTML response is parsed to extract media information.

## 3. Overseerr Integration

- ListSync interacts with the Overseerr API using the `requests` library.
- It implements minimal rate limiting to prevent overwhelming the Overseerr server and webhooks.
- The tool performs media searches, status checks, and request submissions via API endpoints.

## 4. Intelligent Processing

- ListSync differentiates between movies and TV shows for appropriate handling.
- For TV shows, it determines the number of seasons and requests all available seasons.
- The tool checks if media is already available or requested before submitting new requests.

## 5. Error Handling and Logging

- Comprehensive error handling is implemented for network issues, API errors, and parsing problems.
- ListSync uses Python's `logging` module to maintain detailed logs for troubleshooting.
- Real-time status updates are provided in the console using the `colorama` and `halo` libraries.

## 6. Periodic Syncing

- Users can set up recurring syncs at user-defined intervals.
- A sleep mechanism is implemented that can be interrupted for on-demand actions.

## 7. User Interface

- ListSync presents a user-friendly command-line interface with color-coded outputs.
- ASCII art and banners are displayed for an engaging user experience.
- Summary statistics are provided after each sync operation.

By leveraging these components, ListSync provides a seamless, automated solution for managing your media library through Overseerr.

## 📖 Detailed How It Works Document

### Overview

ListSync is a tool designed to automate the process of syncing your watchlists from platforms like IMDb and Trakt with your media server (Overseerr, Jellyseerr, etc.). It ensures that your media server is always up-to-date with the movies and TV shows you want to watch. Below is a detailed breakdown of how ListSync works.

### Step-by-Step Process

#### 1. **Fetching Watchlists**

ListSync starts by fetching your watchlists from IMDb or Trakt. Here’s how it does it:

- **IMDb Lists**:

  - ListSync can fetch lists from IMDb using list IDs (e.g., `ls123456789`) or URLs.
  - It supports IMDb charts like Top 250, Box Office, MovieMeter, and TVMeter.
  - The tool uses Selenium to scrape the IMDb website, ensuring it can handle dynamic content and pagination.

- **Trakt Lists**:
  - ListSync can fetch lists from Trakt using list IDs or URLs.
  - It uses Selenium to navigate Trakt’s website and extract the list items.

#### 2. **Searching Media on Media Server**

Once the watchlists are fetched, ListSync searches for each item on your media server (Overseerr, Jellyseerr, etc.):

- **Search API**:

  - ListSync uses the media server’s search API to look up each item by title and media type (movie or TV show).
  - It handles various edge cases, such as titles with special characters or multiple results.

- **Year Matching**:
  - For more accurate results, ListSync can use the release year (if available) to find the correct media item.

#### 3. **Requesting Media**

After finding the media item on the server, ListSync checks its availability and requests it if necessary:

- **Availability Check**:

  - ListSync checks if the media is already available or has been requested.
  - It uses the media server’s API to get the current status of the item.

- **Requesting Media**:
  - If the media is not available or requested, ListSync automatically requests it on your behalf.
  - For TV shows, it requests all available seasons.

#### 4. **Syncing Regularly**

ListSync can be configured to sync your watchlists at regular intervals:

- **Sync Interval**:

  - You can set how often ListSync should check and update your watchlists (e.g., every 6 hours).
  - The tool runs in the background and performs the sync automatically.

- **Database Tracking**:
  - ListSync uses a SQLite database to track which items have been synced and their status.
  - This ensures that items are not repeatedly requested or skipped unnecessarily.

### Technical Details

#### **Selenium Integration**

ListSync uses Selenium to fetch watchlists from IMDb and Trakt. This allows it to handle dynamic content and pagination, ensuring all items are retrieved.

#### **API Integration**

ListSync integrates with the media server’s API to search for and request media. It handles API rate limits and retries failed requests.

#### **Database Management**

ListSync uses a SQLite database to store:

- List IDs and types (IMDb, Trakt).
- Synced items and their status (requested, available, etc.).
- Sync intervals and last sync times.

#### **Error Handling**

ListSync includes robust error handling to manage:

- Failed API requests.
- Network issues.
- Invalid list IDs or URLs.
- Media not found on the server.

### Example Workflow

1. **User Configures ListSync**:

   - Adds IMDb and Trakt list IDs.
   - Sets sync interval to 6 hours.

2. **ListSync Fetches Watchlists**:

   - Fetches items from IMDb and Trakt lists.

3. **ListSync Searches Media**:

   - Searches for each item on the media server.

4. **ListSync Requests Media**:

   - Requests items that are not available or already requested.

5. **ListSync Tracks Status**:

   - Updates the database with the status of each item.

6. **ListSync Syncs Regularly**:
   - Repeats the process every 6 hours.

### Conclusion

ListSync automates the process of keeping your media server in sync with your watchlists, saving you time and ensuring you never miss out on your favorite content. With its robust features and easy setup, ListSync is the ultimate tool for managing your media library.

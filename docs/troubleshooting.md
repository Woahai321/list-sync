# Troubleshooting Guide

If you're experiencing issues with ListSync, this guide covers common problems and their solutions.

## 1. Invalid API Credentials

**Symptom:** Error messages related to API authentication or 401 Unauthorized responses.

**Solution:**

- Double-check your Overseerr URL and API key in the Overseerr settings.
- Ensure there are no trailing spaces in the URL or API key.
- Try regenerating your API key in Overseerr and updating the script's configuration.

## 2. Script Crashes or Unexpected Behavior

**Symptom:** Script terminates unexpectedly or produces unexpected results.

**Solution:**

- Check the `overseerr_sync.log` file in the `./data` directory for detailed error messages.
- Look for Python tracebacks which can pinpoint the exact line causing the issue.
- Ensure all required Python libraries are installed and up-to-date.
- Verify that your Python version meets the minimum requirements (Python 3.7+).

## 3. Failed to Fetch List

**Symptom:** Error messages indicating failure to retrieve IMDB or Trakt lists.

**Solution:**

- Verify that the list ID is correct and the list is publicly accessible.
- Check your internet connection and firewall settings.
- For IMDB lists, ensure the list URL follows the format: `https://www.imdb.com/list/ls012345678/`
- For Trakt lists, confirm the list URL is in the format: `https://trakt.tv/lists/1234567`

## 4. Decryption Error

**Symptom:** Unable to decrypt configuration or "Incorrect password" error.

**Solution:**

- Ensure you're entering the correct password used during initial setup.
- If you've forgotten the password, delete the `config.enc` file in the `./data` directory and run the script again to reconfigure.
- Check file permissions to ensure the script has read/write access to the `./data` directory.

## 5. Rate Limiting Issues

**Symptom:** Frequent "Too Many Requests" errors or slow processing.

**Solution:**

- Increase the delay between requests by adjusting the `time.sleep()` value in the script.
- Consider reducing the size of your lists or splitting them into smaller chunks.

## 6. Media Not Found in Overseerr

**Symptom:** Many items reported as "Not found" during processing.

**Solution:**

- Verify that Overseerr is properly connected to your media sources (Radarr/Sonarr).
- Check if the titles in your lists match exactly with how they appear in Overseerr's search.
- For TV shows, try using the original title rather than localized versions.

## Still Having Issues?

If you're encountering persistent issues not covered here, please remember that ListSync is in beta development and you may encounter bugs. We appreciate your patience and feedback as we continue to improve the tool.

For additional support, please raise an issue on the GitHub repository with a detailed description of your problem and any relevant log files.

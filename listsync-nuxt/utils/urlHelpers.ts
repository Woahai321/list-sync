/**
 * Utility functions for URL handling and display
 */

/**
 * Extract the final segment of a URL for cleaner display
 * @param url - The URL to extract the segment from
 * @returns The final meaningful segment of the URL
 */
export function extractUrlSegment(url: string): string {
  try {
    // If it's already a simple ID (no URL), return as is
    if (!url.includes('://') && !url.includes('/')) {
      return url
    }
    
    // Parse the URL and extract the final segment
    const urlObj = new URL(url)
    const pathSegments = urlObj.pathname.split('/').filter(segment => segment.length > 0)
    
    // Get the last non-empty segment
    const finalSegment = pathSegments[pathSegments.length - 1]
    
    // If the final segment is empty, try the second-to-last
    if (!finalSegment) {
      return pathSegments[pathSegments.length - 2] || url
    }
    
    // If the final segment is just a number and we have a previous segment, 
    // prefer the previous segment (e.g., "path/to/123" -> "to")
    if (/^\d+$/.test(finalSegment) && pathSegments.length > 1) {
      const previousSegment = pathSegments[pathSegments.length - 2]
      if (previousSegment && !/^\d+$/.test(previousSegment)) {
        return previousSegment
      }
    }
    
    return finalSegment
  } catch (error) {
    // If URL parsing fails, return the original string
    return url
  }
}

/**
 * Format a list ID for display in the UI
 * @param listId - The list ID (may be a URL)
 * @returns A clean display name for the list
 */
export function formatListIdForDisplay(listId: string): string {
  return extractUrlSegment(listId)
}

/**
 * Construct the full URL for a list based on its type and ID.
 * This matches the Python construct_list_url function.
 * @param listType - Type of list (imdb, trakt, trakt_special, letterboxd, anilist, mdblist, stevenlu, tmdb, simkl, tvdb)
 * @param listId - List ID or URL
 * @returns Full URL for the list
 */
export function constructListUrl(listType: string, listId: string): string {
  // If it's already a full URL, return as is
  if (listId.startsWith('http://') || listId.startsWith('https://')) {
    return listId
  }

  const type = listType.toLowerCase()

  // IMDb
  if (type === 'imdb') {
    // Handle special chart names
    if (['top', 'boxoffice', 'moviemeter', 'tvmeter'].includes(listId)) {
      return `https://www.imdb.com/chart/${listId}`
    }
    // Handle user watchlist format
    if (listId.startsWith('ur')) {
      return `https://www.imdb.com/user/${listId}/watchlist`
    }
    // Handle regular list format
    if (listId.startsWith('ls')) {
      return `https://www.imdb.com/list/${listId}`
    }
    // Fallback
    return `https://www.imdb.com/list/${listId}`
  }

  // Trakt and Trakt Special
  if (type === 'trakt' || type === 'trakt_special') {
    // Handle numeric list IDs (regular trakt lists)
    if (/^\d+$/.test(listId)) {
      return `https://trakt.tv/lists/${listId}`
    }
    // Handle special Trakt lists (shortcuts)
    if (listId.includes(':')) {
      const parts = listId.split(':')
      if (parts.length === 2) {
        const [listName, mediaType] = parts
        if (mediaType.toLowerCase() === 'movies') {
          return `https://trakt.tv/movies/${listName}`
        }
        if (['tv', 'shows'].includes(mediaType.toLowerCase())) {
          return `https://trakt.tv/shows/${listName}`
        }
      }
    }
    // Handle special list names without colon (for trakt_special)
    if (type === 'trakt_special') {
      const specialMappings: Record<string, string> = {
        'trending:movies': 'https://trakt.tv/movies/trending',
        'popular:movies': 'https://trakt.tv/movies/popular',
        'anticipated:movies': 'https://trakt.tv/movies/anticipated',
        'watched:movies': 'https://trakt.tv/movies/watched',
        'boxoffice:movies': 'https://trakt.tv/movies/boxoffice',
        'trending:shows': 'https://trakt.tv/shows/trending',
        'popular:shows': 'https://trakt.tv/shows/popular',
        'anticipated:shows': 'https://trakt.tv/shows/anticipated',
        'watched:shows': 'https://trakt.tv/shows/watched'
      }

      if (listId in specialMappings) {
        return specialMappings[listId]
      }

      // If not in mappings, try to construct from the list_id format
      if (['trending', 'popular', 'anticipated', 'watched', 'boxoffice'].some(prefix => listId.startsWith(prefix))) {
        const parts = listId.includes(':') ? listId.split(':') : [listId, 'movies']
        if (parts.length === 2) {
          const [listName, mediaType] = parts
          if (mediaType.toLowerCase() === 'movies') {
            return `https://trakt.tv/movies/${listName}`
          }
          if (['tv', 'shows'].includes(mediaType.toLowerCase())) {
            return `https://trakt.tv/shows/${listName}`
          }
        }
      }
    }
    // Fallback
    return `https://trakt.tv/lists/${listId}`
  }

  // Letterboxd
  if (type === 'letterboxd') {
    return `https://letterboxd.com/${listId}`
  }

  // MDBList
  if (type === 'mdblist') {
    return `https://mdblist.com/lists/${listId}`
  }

  // Steven Lu
  if (type === 'stevenlu') {
    return 'https://movies.stevenlu.com/'
  }

  // TMDB
  if (type === 'tmdb') {
    if (/^\d+$/.test(listId)) {
      return `https://www.themoviedb.org/list/${listId}`
    }
    return listId
  }

  // Simkl
  if (type === 'simkl') {
    if (/^\d+$/.test(listId)) {
      return `https://simkl.com/5/list/${listId}`
    }
    return listId
  }

  // AniList
  if (type === 'anilist') {
    if (listId.includes('/animelist')) {
      return `https://anilist.co/user/${listId}`
    }
    return `https://anilist.co/user/${listId}/animelist`
  }

  // TVDB
  if (type === 'tvdb') {
    if (/^\d+$/.test(listId)) {
      return `https://www.thetvdb.com/lists/${listId}`
    }
    return listId
  }

  // Collections don't have URLs
  if (type === 'collections') {
    return `collection:${listId}`
  }

  // Unknown list type, return the ID as-is
  return listId
}
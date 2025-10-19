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

"""
Discord webhook notifications for ListSync.
"""

import logging
import os
import time
from typing import Optional

try:
    from discord_webhook import DiscordEmbed, DiscordWebhook
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logging.warning("discord_webhook not available. Discord notifications will be disabled.")



def get_discord_webhook_url():
    """
    Get Discord webhook URL from environment variable.
    
    Returns:
        str or None: Discord webhook URL if configured, None otherwise
    """
    return os.getenv("DISCORD_WEBHOOK_URL")


def send_to_discord_webhook(summary_text, sync_results, webhook_url: Optional[str] = None):
    """Send the sync summary to a Discord webhook."""
    if not DISCORD_AVAILABLE:
        return

    # Get webhook URL from parameter or environment
    if not webhook_url:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        return  # No webhook configured

    try:
        processing_time = time.time() - sync_results.start_time
        total_items = sync_results.total_items or 1

        # Calculate success rate and determine embed color
        successful_items = (sync_results.results["requested"] +
                          sync_results.results["already_available"] +
                          sync_results.results["already_requested"] +
                          sync_results.results["skipped"])  # Include skipped items as successful
        success_rate = (successful_items / total_items) * 100 if total_items > 0 else 0

        # Dynamic color based on success rate
        if success_rate >= 80:
            embed_color = "00ff00"  # Green
            status_emoji = "🟢"
        elif success_rate >= 50:
            embed_color = "ffff00"  # Yellow
            status_emoji = "🟡"
        else:
            embed_color = "ff0000"  # Red
            status_emoji = "🔴"

        # Create progress bar for success rate
        progress_length = 10
        filled_length = int(progress_length * success_rate / 100)
        progress_bar = "█" * filled_length + "░" * (progress_length - filled_length)

        # Format numbers with separators
        def format_number(num):
            return f"{num:,}"

        # Format time nicely
        def format_time(seconds):
            if seconds < 60:
                return f"{seconds:.1f}s"
            if seconds < 3600:
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                return f"{minutes}m {secs}s"
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

        # Create webhook instance
        webhook = DiscordWebhook(url=webhook_url, username="Soluify List Sync")

        # Create embed with success rate summary at the top
        embed = DiscordEmbed(
            title="📊 List Sync Summary",
            description=(
                f"{status_emoji} **Success Rate: {success_rate:.1f}% ({format_number(successful_items)}/{format_number(total_items)} items)**\n"
                f"{progress_bar} `{success_rate:.1f}%`\n\n"
                f"Results of the latest sync operation"
            ),
            color=embed_color,
        )

        # Add Processing Stats with better formatting
        avg_time_ms = (processing_time / total_items) * 1000
        embed.add_embed_field(
            name="⏱️ Processing Stats",
            value=(
                f"Total Items: **{format_number(sync_results.total_items)}**\n"
                f"Total Time: **{format_time(processing_time)}**\n"
                f"Avg Time: **{avg_time_ms:.1f}ms/item**"
            ),
            inline=False,
        )

        # Add Status Summary with formatted numbers
        embed.add_embed_field(
            name="📋 Status Summary",
            value=(
                f"✅ Requested: **{format_number(sync_results.results['requested'])}**\n"
                f"☑️ Available: **{format_number(sync_results.results['already_available'])}**\n"
                f"📌 Already Requested: **{format_number(sync_results.results['already_requested'])}**\n"
                f"⏭️ Skipped: **{format_number(sync_results.results['skipped'])}**"
            ),
            inline=False,
        )

        # Add Media Types (only if there's a meaningful breakdown)
        if sync_results.media_type_counts["movie"] > 0 and sync_results.media_type_counts["tv"] > 0:
            embed.add_embed_field(
                name="🎬 Media Types",
                value=(
                    f"Movies: **{format_number(sync_results.media_type_counts['movie'])}** ({sync_results.media_type_counts['movie']/total_items*100:.1f}%)\n"
                    f"TV Shows: **{format_number(sync_results.media_type_counts['tv'])}** ({sync_results.media_type_counts['tv']/total_items*100:.1f}%)"
                ),
                inline=False,
            )

        # Add Synced Lists section
        if sync_results.synced_lists:
            synced_lists_text = ""
            for list_info in sync_results.synced_lists:
                list_type = list_info.get("type", "Unknown").upper()
                list_url = list_info.get("url", "No URL")
                item_count = list_info.get("item_count", 0)

                # Handle different list types and URL formats
                if list_url.startswith(("http://", "https://")):
                    # Regular URLs - make them clickable
                    synced_lists_text += f"✅ **{list_type}**: [{item_count} items]({list_url})\n"
                elif list_type == "TRAKT_SPECIAL" and ":" in list_url:
                    # Convert Trakt special shortcut to full URL (e.g., "trending:movies" -> "https://trakt.tv/movies/trending")
                    parts = list_url.split(":")
                    if len(parts) == 2:
                        list_category, media_type = parts
                        if media_type.lower() in ["movies", "movie"]:
                            full_url = f"https://trakt.tv/movies/{list_category}"
                        elif media_type.lower() in ["shows", "show", "tv"]:
                            full_url = f"https://trakt.tv/shows/{list_category}"
                        else:
                            full_url = list_url  # Fallback to original if unknown format
                        synced_lists_text += f"✅ **{list_type}**: [{item_count} items]({full_url})\n"
                    else:
                        # Fallback for invalid format
                        synced_lists_text += f"✅ **{list_type}**: {item_count} items - {list_url}\n"
                else:
                    # Non-URL entries or regular list IDs
                    synced_lists_text += f"✅ **{list_type}**: {item_count} items\n"

            embed.add_embed_field(
                name="📚 Synced Lists",
                value=synced_lists_text,
                inline=False,
            )

        # Add Not Found Items if any (using spoiler tags for expandable sections)
        all_failed_items = []

        # Add not found items
        for item in sync_results.not_found_items:
            all_failed_items.append(f"• {item['title']} (Not Found)")

        # Add error items
        for item in sync_results.error_items:
            error_msg = item.get("error", "Unknown error")
            all_failed_items.append(f"• {item['title']} (Error: {error_msg})")

        # Only show failed items section if there are failures
        if all_failed_items:
            not_found_text = ""
            for i, item_line in enumerate(all_failed_items[:10]):
                # Use spoiler tags to make it collapsible
                not_found_text += f"||{item_line}||\n"

            if len(all_failed_items) > 10:
                not_found_text += f"||... and {len(all_failed_items) - 10} more||\n"

            not_found_text += "\n*Click to expand failed items*"

            embed.add_embed_field(
                name=f"❓ Failed Items ({format_number(len(all_failed_items))})",
                value=not_found_text,
                inline=False,
            )

        # Set timestamp
        embed.set_timestamp()

        # Add footer
        embed.set_footer(text="Soluify List Sync Tool | v0.5.8")

        # Add embed to webhook
        webhook.add_embed(embed)

        # Send webhook
        webhook.execute()
        logging.info("Discord webhook notification sent successfully")
    except Exception as e:
        logging.exception(f"Failed to send Discord webhook notification: {e!s}")

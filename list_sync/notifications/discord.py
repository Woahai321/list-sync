"""
Discord webhook notifications for ListSync.
"""

import logging
import os
import time
from typing import Optional, Dict, Any

try:
    from discord_webhook import DiscordWebhook, DiscordEmbed
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logging.warning("discord_webhook not available. Discord notifications will be disabled.")

from ..ui.display import SyncResults


def get_discord_webhook_url():
    """
    Get Discord webhook URL from environment variable.
    
    Returns:
        str or None: Discord webhook URL if configured, None otherwise
    """
    return os.getenv('DISCORD_WEBHOOK_URL')


def send_to_discord_webhook(summary_text, sync_results, webhook_url: Optional[str] = None, automated: bool = False):
    """Send enhanced multi-embed Discord notification with rich context."""
    if not DISCORD_AVAILABLE:
        return
    
    # Get webhook URL from parameter or environment
    if not webhook_url:
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        return  # No webhook configured
    
    try:
        # Collect enhanced data
        enhanced_data = collect_enhanced_sync_data(sync_results, automated)
        
        # Build single embed
        webhook = DiscordWebhook(url=webhook_url, username="ListSync")
        embed = build_summary_embed(enhanced_data)
        webhook.add_embed(embed)
        
        webhook.execute()
        logging.info("Enhanced Discord notification sent successfully")
        
    except Exception as e:
        logging.error(f"Failed to send enhanced Discord notification: {str(e)}")


def collect_enhanced_sync_data(sync_results: SyncResults, automated: bool = False) -> Dict[str, Any]:
    """Collect data for enhanced notifications."""
    return {
        'sync_results': sync_results,
        'automated': automated,
        'processing_time': time.time() - sync_results.start_time
    }


def build_summary_embed(data: Dict[str, Any]) -> DiscordEmbed:
    """Build a beautiful, comprehensive summary embed with all Discord features."""
    sync_results = data['sync_results']
    processing_time = data['processing_time']
    
    total_items = sync_results.total_items or 1
    successful_items = (sync_results.results['requested'] + 
                       sync_results.results['already_available'] + 
                       sync_results.results['already_requested'] +
                       sync_results.results['skipped'])
    success_rate = (successful_items / total_items) * 100 if total_items > 0 else 0
    failed_items = sync_results.results['not_found'] + sync_results.results['error']
    
    # Dynamic styling based on success rate
    if success_rate >= 95:
        color = "00ff88"  # Bright green
        status_emoji = "✨"
        status_text = "Perfect"
    elif success_rate >= 80:
        color = "00dd66"  # Green
        status_emoji = "✅"
        status_text = "Excellent"
    elif success_rate >= 60:
        color = "ffaa00"  # Orange
        status_emoji = "⚠️"
        status_text = "Good"
    else:
        color = "ff4444"  # Red
        status_emoji = "❌"
        status_text = "Needs Attention"
    
    # Build title with emoji
    sync_mode = "🎬 Media" if data['automated'] else "🎬 Media"
    title = f"{status_emoji} {sync_mode} Sync Complete"
    
    # Create progress bar visualization
    progress_bar = create_progress_bar(success_rate)
    
    # Rich description with key metrics
    movies = sync_results.media_type_counts['movie']
    shows = sync_results.media_type_counts['tv']
    
    description = (
        f"### {progress_bar} **{success_rate:.1f}%** Success Rate\n\n"
        f"**{successful_items:,}** of **{total_items:,}** items processed successfully\n"
        f"⏱️ Completed in **{format_time(processing_time)}** "
    )
    
    embed = DiscordEmbed(
        title=title,
        description=description,
        color=color
    )
    
    # Set author for branding
    embed.set_author(
        name="ListSync",
        icon_url="https://s.2ya.me/api/shares/RN2Yziau/files/535b57e0-9c64-410b-a36f-414fba74854b"
    )
    
    # === QUICK STATS (Inline for compact view) ===
    embed.add_embed_field(
        name="🎬 Movies",
        value=f"**{movies:,}**\n{get_percentage_text(movies, total_items)}",
        inline=True
    )
    
    embed.add_embed_field(
        name="📺 TV Shows",
        value=f"**{shows:,}**\n{get_percentage_text(shows, total_items)}",
        inline=True
    )
    
    embed.add_embed_field(
        name="⚡ Speed",
        value=f"**{format_avg_time(processing_time, total_items)}**\nper item",
        inline=True
    )
    
    # === RESULTS BREAKDOWN ===
    results_lines = []
    
    if sync_results.results['requested'] > 0:
        results_lines.append(
            f"✅ **{sync_results.results['requested']:,}** New Requests Sent"
        )
    
    if sync_results.results['already_available'] > 0:
        results_lines.append(
            f"💚 **{sync_results.results['already_available']:,}** Already Available"
        )
    
    if sync_results.results['already_requested'] > 0:
        results_lines.append(
            f"📌 **{sync_results.results['already_requested']:,}** Already Requested"
        )
    
    if sync_results.results['skipped'] > 0:
        results_lines.append(
            f"⏭️ **{sync_results.results['skipped']:,}** Skipped (Recent)"
        )
    
    if failed_items > 0:
        results_lines.append(
            f"❌ **{failed_items:,}** Failed"
        )
    
    results_text = "\n".join(results_lines) if results_lines else "No items processed"
    
    embed.add_embed_field(
        name="📊 Results Breakdown",
        value=results_text,
        inline=False
    )
    
    # === SYNCED LISTS ===
    if sync_results.synced_lists:
        lists_lines = []
        for idx, list_info in enumerate(sync_results.synced_lists[:5], 1):
            list_type = list_info.get('type', 'Unknown').upper()
            item_count = list_info.get('item_count', 0)
            list_url = list_info.get('url', '')
            
            # Get emoji for list type
            list_emoji = get_list_emoji(list_type)
            
            if list_url and list_url.startswith(('http://', 'https://')):
                lists_lines.append(
                    f"{list_emoji} **[{list_type}]({list_url})** — {item_count:,} items"
                )
            else:
                lists_lines.append(
                    f"{list_emoji} **{list_type}** — {item_count:,} items"
                )
        
        if len(sync_results.synced_lists) > 5:
            remaining = len(sync_results.synced_lists) - 5
            lists_lines.append(f"*... and {remaining} more list{'s' if remaining > 1 else ''}*")
        
        embed.add_embed_field(
            name="📋 Synced Lists",
            value="\n".join(lists_lines),
            inline=False
        )
    
    # === ERRORS (if any) ===
    if failed_items > 0:
        error_items = sync_results.not_found_items[:3]  # Show max 3
        error_lines = []
        
        for item in error_items:
            title = item.get('title', 'Unknown')
            # Truncate long titles
            if len(title) > 40:
                title = title[:37] + "..."
            error_lines.append(f"• {title}")
        
        if len(sync_results.not_found_items) > 3:
            remaining = len(sync_results.not_found_items) - 3
            error_lines.append(f"*... and {remaining} more*")
        
        if error_lines:
            embed.add_embed_field(
                name="⚠️ Not Found",
                value="\n".join(error_lines),
                inline=False
            )
    
    # === FOOTER ===
    embed.set_timestamp()
    footer_text = "ListSync v0.6.3"
    if total_items > 100:
        footer_text += f" • {total_items:,} items"
    embed.set_footer(text=footer_text)
    
    return embed


def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Create a visual progress bar using Discord emojis."""
    filled = int((percentage / 100) * length)
    empty = length - filled
    
    # Use block characters for progress bar
    bar = "█" * filled + "░" * empty
    return f"`{bar}`"


def get_percentage_text(count: int, total: int) -> str:
    """Get percentage as formatted text."""
    if total == 0:
        return "0%"
    percentage = (count / total) * 100
    return f"{percentage:.1f}%"


def format_avg_time(total_seconds: float, total_items: int) -> str:
    """Format average processing time per item."""
    if total_items == 0:
        return "0ms"
    
    avg_ms = (total_seconds / total_items) * 1000
    
    if avg_ms < 1:
        return f"{avg_ms:.2f}ms"
    elif avg_ms < 1000:
        return f"{avg_ms:.0f}ms"
    else:
        return f"{avg_ms/1000:.1f}s"


def get_list_emoji(list_type: str) -> str:
    """Get appropriate emoji for list type."""
    list_type_upper = list_type.upper()
    
    emoji_map = {
        'TRAKT': '🎬',
        'IMDB': '⭐',
        'LETTERBOXD': '🎞️',
        'MDBLIST': '📊',
        'SIMKL': '📱',
        'TMDB': '🎯',
        'TVDB': '📺',
        'STEVENLU': '🎥',
    }
    
    return emoji_map.get(list_type_upper, '📋')






def format_time(seconds: float) -> str:
    """Format time duration nicely."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

# Instagram Scraping Patterns

## Reels View Counts (No Login Required)

Instagram's web interface displays reel view counts as text overlays on thumbnails in the Reels tab — no authentication needed.

**URL pattern:** `https://www.instagram.com/{username}/reels/`

**Method:**
1. `browser_navigate` to the reels URL
2. `browser_snapshot` with `full=true` to capture the grid
3. Parse view counts from link text (e.g., `"View Count Icon 2.8M"`)
4. Scroll down to load more reels if needed

**Pitfall:** Instagram may show a login modal on first visit. Dismiss it via the Close button — the reels grid is usually still accessible underneath.

## Profile Metadata

Follower/following counts and bio text are visible on the profile header without login. The bio often contains contact info for collaborations.

## Verifying Reel URLs Before Sharing

**Never share a reel URL from web search results without verifying it belongs to the correct account.** Web search can return reels from other accounts that happen to have similar view counts. Always cross-check the URL against the actual profile page or use `browser_navigate` to confirm the reel appears on the expected account.

## Reels Grid Rendering Issues

The reels grid may not render properly even when the page loads:
- The profile header (followers, bio) may appear but the reel thumbnails with view counts may be absent from the DOM
- This can happen due to Instagram's lazy loading, bot detection, or JavaScript execution issues
- If `browser_snapshot` shows no reel links, try scrolling down or waiting a few seconds
- If the grid still doesn't render, inform the user rather than guessing URLs

## General Notes

- Instagram's DOM uses generic class names; rely on `StaticText` content and `link` hrefs for data extraction
- View counts use K/M suffixes (e.g., `55.3K`, `2.8M`) — parse accordingly
- The reels grid loads lazily; scroll to reveal more content
- When the CDP connection drops, relaunch Chrome with `--remote-debugging-port=9222` and retry

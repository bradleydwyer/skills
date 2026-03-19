# YouTube Data API v3 — Endpoint Reference

## Search (100 quota units)

`GET /youtube/v3/search`

| Parameter | Type | Description |
|---|---|---|
| q | string | Search query |
| type | string | `video`, `channel`, `playlist` (comma-separated OK) |
| maxResults | int | 1–50 (default 5) |
| order | string | `relevance`, `date`, `rating`, `viewCount`, `title` |
| channelId | string | Restrict to a specific channel |
| publishedAfter | datetime | ISO 8601 (e.g. `2024-01-01T00:00:00Z`) |
| publishedBefore | datetime | ISO 8601 |
| regionCode | string | ISO 3166-1 alpha-2 (e.g. `US`) |
| relevanceLanguage | string | ISO 639-1 (e.g. `en`) |
| videoDuration | string | `any`, `short` (<4min), `medium` (4-20min), `long` (>20min) |
| videoDefinition | string | `any`, `high`, `standard` |
| pageToken | string | Pagination token |

**Response fields:** `items[].id.videoId`, `items[].snippet.title`, `.description`, `.channelTitle`, `.publishedAt`, `.thumbnails`

---

## Videos (1 quota unit)

`GET /youtube/v3/videos`

| Parameter | Type | Description |
|---|---|---|
| id | string | Comma-separated video IDs (max 50) |
| part | string | `snippet`, `statistics`, `contentDetails`, `topicDetails`, `status`, `player`, `liveStreamingDetails` |

**Key response fields by part:**

- **snippet**: `title`, `description`, `channelId`, `channelTitle`, `tags[]`, `categoryId`, `publishedAt`, `thumbnails`, `defaultLanguage`
- **statistics**: `viewCount`, `likeCount`, `commentCount`
- **contentDetails**: `duration` (ISO 8601, e.g. `PT4M13S`), `dimension`, `definition`, `caption`, `licensedContent`
- **topicDetails**: `topicCategories[]` (Wikipedia URLs)

---

## Channels (1 quota unit)

`GET /youtube/v3/channels`

| Parameter | Type | Description |
|---|---|---|
| id | string | Channel ID |
| forUsername | string | Legacy username |
| forHandle | string | Channel handle (e.g. `@mkbhd`) |
| part | string | `snippet`, `statistics`, `contentDetails`, `brandingSettings`, `topicDetails` |

**Key response fields:**

- **snippet**: `title`, `description`, `customUrl`, `publishedAt`, `thumbnails`, `country`
- **statistics**: `viewCount`, `subscriberCount`, `videoCount`
- **contentDetails**: `relatedPlaylists.uploads` (playlist ID for all uploads)
- **brandingSettings**: `channel.keywords`, `image.bannerExternalUrl`

---

## Comment Threads (1 quota unit)

`GET /youtube/v3/commentThreads`

| Parameter | Type | Description |
|---|---|---|
| videoId | string | Video ID |
| part | string | `snippet`, `replies` |
| maxResults | int | 1–100 (default 20) |
| order | string | `relevance`, `time` |
| searchTerms | string | Filter by keyword |
| pageToken | string | Pagination token |

**Response fields:** `items[].snippet.topLevelComment.snippet.textDisplay`, `.authorDisplayName`, `.likeCount`, `.publishedAt`, `items[].snippet.totalReplyCount`

---

## Playlist Items (1 quota unit)

`GET /youtube/v3/playlistItems`

| Parameter | Type | Description |
|---|---|---|
| playlistId | string | Playlist ID |
| part | string | `snippet`, `contentDetails`, `status` |
| maxResults | int | 1–50 (default 5) |
| pageToken | string | Pagination token |

**Response fields:** `items[].snippet.title`, `.description`, `.channelTitle`, `.position`, `.resourceId.videoId`, `items[].contentDetails.videoPublishedAt`

---

## Captions (50 quota units)

`GET /youtube/v3/captions`

| Parameter | Type | Description |
|---|---|---|
| videoId | string | Video ID |
| part | string | `snippet` |

**Response fields:** `items[].snippet.language`, `.name`, `.trackKind` (`standard`, `ASR`), `.audioTrackType`, `.isAutoSynced`

Note: Listing captions works with an API key. Downloading caption content requires OAuth with the video owner's authorization. For transcripts of videos you don't own, use yt-dlp instead.

---

## Quota Summary

| Endpoint | Cost |
|---|---|
| search | 100 |
| videos.list | 1 |
| channels.list | 1 |
| commentThreads.list | 1 |
| playlistItems.list | 1 |
| captions.list | 50 |
| captions.download | 200 (OAuth required) |

Daily limit: 10,000 units. A single search costs 100 units, so prefer direct lookups with IDs when possible.

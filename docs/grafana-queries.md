# Grafana SQL Queries for Video Enhancer

This document contains ready-to-use SQL queries for Grafana dashboards.

## Basic Statistics

### Total Transcodings
```sql
SELECT COUNT(*) as total FROM transcodings;
```
**Use in**: Stat panel, Single stat
**Returns**: Total number of videos processed

### Transcodings by Status
```sql
SELECT 
  status,
  COUNT(*) as count
FROM transcodings
GROUP BY status
ORDER BY count DESC;
```
**Use in**: Pie chart, Bar chart, Table
**Returns**: Count of videos grouped by status. Possible statuses:
- `pending`: Waiting to be processed
- `in_progress`: Currently being transcoded
- `completed`: Successfully transcoded
- `not_required`: Video already in correct format, no transcoding needed
- `failed`: Transcoding failed with error

### Success Rate
```sql
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
  SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
  SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
  SUM(CASE WHEN status = 'not_required' THEN 1 ELSE 0 END) as not_required,
  ROUND(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_percent
FROM transcodings;
```
**Use in**: Table, Stat panels
**Returns**: Breakdown by status and success rate percentage

## Detailed Views

### Failed Videos with Error Messages
```sql
SELECT 
  original_video_path,
  error_message,
  transcoded_video_codec,
  transcoded_video_resolution
FROM transcodings
WHERE status = 'failed'
ORDER BY original_video_path;
```
**Use in**: Table panel
**Returns**: List of failed videos with error details

### Completed Transcodings by Codec
```sql
SELECT 
  transcoded_video_codec,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transcodings WHERE status = 'completed'), 2) as percentage
FROM transcodings
WHERE status = 'completed'
GROUP BY transcoded_video_codec
ORDER BY count DESC;
```
**Use in**: Pie chart, Bar chart
**Returns**: Distribution of completed transcodings by codec (h264, hevc, etc.)

### Completed Transcodings by Resolution
```sql
SELECT 
  transcoded_video_resolution,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transcodings WHERE status = 'completed'), 2) as percentage
FROM transcodings
WHERE status = 'completed'
GROUP BY transcoded_video_resolution
ORDER BY count DESC;
```
**Use in**: Pie chart, Bar chart
**Returns**: Distribution of completed transcodings by resolution (1920x1080, 1280x720, etc.)

## Summary Dashboard Queries

### Overall Statistics (Single Row)
```sql
SELECT 
  COUNT(*) as total_videos,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
  SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
  SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
  SUM(CASE WHEN status = 'not_required' THEN 1 ELSE 0 END) as not_required,
  ROUND(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM transcodings;
```
**Use in**: Stat panels (one panel per column)
**Returns**: Single row with all key metrics

### Top 10 Failed Videos
```sql
SELECT 
  original_video_path as "Video Path",
  error_message as "Error",
  transcoded_video_codec as "Codec",
  transcoded_video_resolution as "Resolution"
FROM transcodings
WHERE status = 'failed'
ORDER BY original_video_path
LIMIT 10;
```
**Use in**: Table panel
**Returns**: Top 10 failed videos for quick debugging

### Codec Distribution
```sql
SELECT 
  transcoded_video_codec as codec,
  COUNT(*) as count
FROM transcodings
WHERE status = 'completed'
GROUP BY transcoded_video_codec
ORDER BY count DESC;
```
**Use in**: Pie chart, Bar chart
**Returns**: How many videos were transcoded to each codec

## Advanced Queries

### Videos That Don't Need Transcoding
```sql
SELECT COUNT(*) as count
FROM transcodings
WHERE status = 'completed' 
  AND original_video_path = transcoded_video_path;
```
**Use in**: Stat panel
**Returns**: Count of videos that were already in the correct format

### Error Summary
```sql
SELECT 
  SUBSTR(error_message, 1, 100) as error_summary,
  COUNT(*) as occurrences
FROM transcodings
WHERE status = 'failed' AND error_message IS NOT NULL
GROUP BY error_summary
ORDER BY occurrences DESC
LIMIT 10;
```
**Use in**: Table panel
**Returns**: Most common error messages

### Resolution Statistics
```sql
SELECT 
  transcoded_video_resolution,
  COUNT(*) as count,
  MIN(transcoded_video_resolution) as min_res,
  MAX(transcoded_video_resolution) as max_res
FROM transcodings
WHERE status = 'completed'
GROUP BY transcoded_video_resolution
ORDER BY count DESC;
```
**Use in**: Table panel
**Returns**: Resolution distribution with min/max

## Panel Configuration Tips

### For Stat Panels:
- Use single-value queries (e.g., `SELECT COUNT(*) as total FROM transcodings`)
- Set "Value options" → "Show" to "Value"
- Add thresholds for success rate (green > 90%, yellow > 70%, red < 70%)

### For Pie Charts:
- Use queries with GROUP BY
- Set "Label" to the grouping column (status, codec, etc.)
- Set "Value" to the count column

### For Tables:
- Use queries that return multiple columns
- Enable "Transform" → "Organize fields" to rename columns
- Add "Cell display mode" for better formatting

### For Bar Charts:
- Use queries with GROUP BY
- Set X-axis to the grouping column
- Set Y-axis to the count/percentage column


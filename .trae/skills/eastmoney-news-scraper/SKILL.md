---
name: "eastmoney-news-scraper"
description: "Implements 24/7 news scraping from East Money using Scrapy and MongoDB. Invoke when users need to build similar web scraping systems for financial news or JSONP APIs."
---

# East Money News Scraper

This skill provides a comprehensive guide for building a 24/7 news scraping system for East Money (东方财富) using Scrapy and MongoDB.

## Overview

The East Money News Scraper implements a complete pipeline for:
- Scraping 24-hour financial news from East Money API
- Processing JSONP format responses
- Storing data in MongoDB with deduplication
- Implementing scheduled scraping every 5 minutes
- Managing incremental data collection

## When to Use

**Invoke this skill when:**
- Building web scrapers for financial news websites
- Working with JSONP format APIs
- Implementing scheduled data collection systems
- Setting up MongoDB storage with deduplication
- Creating production-ready scraping pipelines

## Project Structure

```
python-web-scraper/
├── configs/
│   └── config.json          # Configuration settings
├── internal/
│   ├── spider/              # Scrapy spider implementation
│   ├── pipeline/            # Data processing pipelines
│   ├── storage/             # MongoDB storage implementation
│   ├── scheduler/           # Scheduled task management
│   └── utils/               # Utility functions
├── tests/                   # Test cases
├── requirements.txt         # Dependencies
└── main.py                  # Main entry point
```

## Key Components

### 1. Spider Implementation

The `EastMoneyNewsSpider` class handles:
- API calls to check for new news (`getFastNewsCount`)
- API calls to fetch news lists (`getFastNewsList`)
- JSONP response parsing
- Incremental data collection with `sortEnd` parameter
- Request tracing with `req_trace` parameter

### 2. Data Storage

The `MongoStorage` class provides:
- MongoDB connection management
- News item storage with deduplication
- Unique index creation for `code` field
- Error handling for storage operations

### 3. Scheduled Task Management

The `NewsScheduler` class implements:
- 5-minute interval scraping
- Progress persistence
- Background thread execution
- Graceful start/stop handling

### 4. Pipeline Processing

The `MongoPipeline` class handles:
- Item validation
- Duplicate checking
- Data storage
- Resource cleanup

## Technical Best Practices

### JSONP Handling

```python
def _parse_jsonp(self, jsonp_str):
    """解析JSONP格式的响应"""
    # 移除jQuery回调包装
    start = jsonp_str.find('(')
    end = jsonp_str.rfind(')')
    if start != -1 and end != -1:
        json_str = jsonp_str[start+1:end]
        return json.loads(json_str)
    return {}
```

### Incremental Collection

- Use `sortEnd` parameter to fetch historical data
- Use `req_trace` parameter for request tracking
- Store progress to resume collection after restarts

### Data Deduplication

- Create unique index on `code` field in MongoDB
- Check for duplicates before storage
- Handle insertion errors gracefully

### Scheduled Execution

- Use `schedule` library for task scheduling
- Run scheduler in a background thread
- Implement error handling for robust operation

## Testing Strategy

- Use Test-Driven Development (TDD) approach
- Write unit tests for key components
- Test JSON parsing and data storage
- Verify pipeline processing

## Deployment Considerations

- Ensure MongoDB is running
- Install required dependencies
- Set appropriate scraping intervals
- Implement logging for monitoring
- Consider rate limiting to avoid API blocks

## Example Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Start the scraper
python main.py
```

## Troubleshooting

### Common Issues

1. **JSONP Parsing Errors**
   - Check response format
   - Verify callback function names

2. **MongoDB Connection Issues**
   - Ensure MongoDB is running
   - Check connection parameters

3. **API Rate Limiting**
   - Adjust scraping interval
   - Implement exponential backoff

4. **Data Duplication**
   - Verify unique index creation
   - Check deduplication logic

## Requirement Analysis Integration

### Application of Requirement Analysis

The East Money News Scraper project benefits from systematic requirement analysis:

#### 1. Requirement Gathering
- **Stakeholder Identification:** Data analysts, financial researchers, application developers
- **Business Requirements:** 24/7 news monitoring, real-time data collection, historical data preservation
- **Technical Requirements:** JSONP API handling, MongoDB storage, scheduled execution
- **User Requirements:** Reliable data collection, deduplicated storage, easy access to news data

#### 2. Requirement Classification
- **Functional Requirements:**
  - Check for new news using `getFastNewsCount` API
  - Fetch news lists using `getFastNewsList` API
  - Process JSONP format responses
  - Store news data in MongoDB with deduplication
  - Schedule regular scraping intervals
- **Non-Functional Requirements:**
  - Reliability: System should run continuously
  - Performance: Minimal resource usage
  - Scalability: Handle increasing news volume
  - Maintainability: Clean, modular code structure

#### 3. Requirement Documentation
- **Use Cases:**
  - UC1: Check for new news updates
  - UC2: Fetch and process news data
  - UC3: Store news with deduplication
  - UC4: Schedule regular scraping
- **Acceptance Criteria:**
  - System collects news every 5 minutes
  - No duplicate news stored
  - JSONP responses parsed correctly
  - System recovers from failures

#### 4. Requirement Validation
- **Technical Feasibility:** Verified API access and MongoDB integration
- **Business Value:** Confirmed need for real-time financial news data
- **User Acceptance:** Validated with potential users

## Conclusion

This skill provides a complete blueprint for building a robust, production-ready news scraping system for East Money. It demonstrates best practices for web scraping, data processing, and scheduled task management that can be applied to similar projects.

By integrating requirement analysis techniques, you can ensure that the system meets stakeholder needs, stays within scope, and delivers business value. The structured approach to requirement analysis helps identify potential issues early and ensures the final implementation aligns with business objectives.

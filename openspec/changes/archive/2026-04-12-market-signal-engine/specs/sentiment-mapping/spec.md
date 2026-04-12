## ADDED Requirements

### Requirement: BK Code Extraction
The system SHALL extract stock list parameters (e.g., `90.Bk100`) from real-time news data.

#### Scenario: Successful BK code parsing
- **WHEN** a news item contains `stockList: ["90.Bk100", "90.Bk205"]`
- **THEN** the system extracts the strings "Bk100" and "Bk205"

### Requirement: Industry Mapping
The system SHALL map extracted BK codes to specific stock tickers using the `data/all_stock_industry.csv` mapping file.

#### Scenario: Mapping Bk100 to stocks
- **WHEN** the extracted code is "Bk100"
- **THEN** the system retrieves all stock symbols associated with the "Bk100" sector from the mapping dictionary

### Requirement: Sentiment-Driven Watchlist Entry
Stocks identified via news BK mapping SHALL be added to the `watch_list` for prioritized monitoring.

#### Scenario: Hotspot stock added to watch_list
- **WHEN** a news item triggers the mapping of stocks for "Bk100"
- **THEN** all non-ST stocks in that sector are added to the `watch_list` with a 24h TTL

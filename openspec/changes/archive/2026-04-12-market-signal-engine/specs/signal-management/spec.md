## ADDED Requirements

### Requirement: Signal Persistence
The system SHALL store all generated market signals in a MongoDB collection for historical tracking and API retrieval.

#### Scenario: Saving a new signal
- **WHEN** a monitoring trigger occurs
- **THEN** the system saves a document containing symbol, signal type, price, volume, and timestamp to the `market_signals` collection

### Requirement: Signal Cooldown (Throttling)
The system MUST prevent the same signal type from triggering for the same stock within a defined cooldown window.

#### Scenario: Suppressing duplicate signals
- **WHEN** a "Price Breakout" signal for "SH600519" was triggered 10 minutes ago
- **THEN** the system SHALL NOT generate another "Price Breakout" signal for the same stock until the 4-hour cooldown expires

### Requirement: Watch-list TTL Management
The system SHALL automatically expire stocks from the `watch_list` based on the source of their entry.

#### Scenario: News-driven stock expiry
- **WHEN** a stock was added to the `watch_list` via a news event 24 hours ago
- **THEN** the system removes the stock from the `watch_list`

## ADDED Requirements

### Requirement: Symbol Normalization
The system SHALL provide a mechanism to normalize any input stock code (e.g., "600000", "sh600000", "600000.SH") into a consistent internal "Golden Standard" format.

#### Scenario: Normalize A-share stock
- **WHEN** user provides "600000" and market is identified as Shanghai
- **THEN** system returns normalized symbol "sh600000"

#### Scenario: Handle various formats
- **WHEN** user provides "sh.600000" or "600000.SH"
- **THEN** system returns normalized symbol "sh600000"

### Requirement: Provider-Specific Formatting
The system SHALL be able to convert the internal normalized symbol back into the specific format required by external data providers (e.g., Akshare, Baostock).

#### Scenario: Convert to Akshare format
- **WHEN** internal symbol is "sh600000" and target provider is "akshare"
- **THEN** system returns "sh600000" (or provider's specific required format)

#### Scenario: Convert to TDX format
- **WHEN** internal symbol is "sh600000" and target provider is "tdx"
- **THEN** system returns "600000"

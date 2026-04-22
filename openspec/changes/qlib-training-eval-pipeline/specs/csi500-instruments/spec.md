## ADDED Requirements

### Requirement: CSI 500 stock list configuration
The system SHALL provide a `CSI_500_STOCKS` list in `config.py` containing stock codes for the 中证500 index, in the same format as the existing `CSI_300_STOCKS` list (e.g., "SH600000", "SZ000001").

#### Scenario: Access CSI 500 stocks
- **WHEN** code calls `get_csi500_instruments()`
- **THEN** a list of 500 stock codes is returned in SH/SZ prefixed format

### Requirement: Instrument selection helper function
The system SHALL provide a `get_instruments(pool_name)` function that accepts "csi300" or "csi500" and returns the corresponding stock list.

#### Scenario: Select CSI 300 pool
- **WHEN** `get_instruments("csi300")` is called
- **THEN** the CSI 300 stock list is returned

#### Scenario: Select CSI 500 pool
- **WHEN** `get_instruments("csi500")` is called
- **THEN** the CSI 500 stock list is returned

#### Scenario: Invalid pool name
- **WHEN** `get_instruments("csi1000")` is called
- **THEN** a ValueError is raised with message indicating valid pool names

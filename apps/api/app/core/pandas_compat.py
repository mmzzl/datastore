"""
Pandas 3.0+ compatibility patch for fillna method parameter.
This patches the deprecated fillna(method=...) syntax.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union

# Store original fillna
_original_fillna = pd.DataFrame.fillna
_original_series_fillna = pd.Series.fillna


def _patched_fillna(
    self,
    value=None,
    method=None,
    axis=None,
    inplace=False,
    limit=None,
    downcast=None,
):
    """
    Patched fillna that handles the removed 'method' parameter in pandas 3.0+.
    
    In pandas 2.0+, the 'method' parameter was deprecated and removed.
    This patch converts old-style calls to new-style methods.
    """
    # If method is specified, convert to appropriate method call
    if method is not None:
        if method == 'ffill' or method == 'pad':
            return self.ffill(axis=axis, inplace=inplace, limit=limit)
        elif method == 'bfill' or method == 'backfill':
            return self.bfill(axis=axis, inplace=inplace, limit=limit)
        else:
            raise ValueError(f"Invalid fillna method: {method}")
    
    # Call original fillna without method/downcast parameters (removed in pandas 3.0+)
    return _original_fillna(
        self,
        value=value,
        axis=axis,
        inplace=inplace,
        limit=limit,
    )


# Apply the patch
pd.DataFrame.fillna = _patched_fillna
pd.Series.fillna = _patched_fillna

print("Pandas compatibility patch applied successfully")

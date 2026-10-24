"""
sutradhar_api/adapters/__init__.py
Canonical Integration Adapters Package for Sutradhar.

Provides simulated adapters that normalize heterogeneous external formats
into canonical Sutradhar data contracts without altering downstream engines.
"""

from sutradhar_api.adapters.banking import BankingFiuAdapter
from sutradhar_api.adapters.base import (
    AdapterError,
    AdapterMappingError,
    AdapterValidationError,
    BaseAdapter,
)
from sutradhar_api.adapters.cctns import CctnsFirAdapter
from sutradhar_api.adapters.kumbh import KumbhOperationsAdapter
from sutradhar_api.adapters.mahacyber import MahaCyberPortalAdapter

__all__ = [
    "AdapterError",
    "AdapterMappingError",
    "AdapterValidationError",
    "BaseAdapter",
    "BankingFiuAdapter",
    "CctnsFirAdapter",
    "KumbhOperationsAdapter",
    "MahaCyberPortalAdapter",
]

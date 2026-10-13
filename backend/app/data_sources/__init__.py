from app.config import settings
from app.data_sources.base import InventoryDataSource
from app.data_sources.local_db_source import LocalDbDataSource
from app.data_sources.external_blood_bank_source import ExternalBloodBankSource

_local_source = LocalDbDataSource()
_external_blood_source = ExternalBloodBankSource()


def get_blood_data_source() -> InventoryDataSource:
    """Returns configured blood inventory source (local or external)."""
    if settings.BLOOD_DATA_SOURCE.lower() == "external":
        return _external_blood_source
    return _local_source


def get_medicine_data_source() -> InventoryDataSource:
    """Returns configured medicine inventory source."""
    return _local_source


def get_bed_data_source() -> InventoryDataSource:
    """Returns configured bed inventory source."""
    return _local_source


__all__ = [
    "InventoryDataSource",
    "LocalDbDataSource",
    "ExternalBloodBankSource",
    "get_blood_data_source",
    "get_medicine_data_source",
    "get_bed_data_source",
]

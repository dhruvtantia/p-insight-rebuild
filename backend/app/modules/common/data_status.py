from datetime import datetime

from pydantic import BaseModel


class DataStatus(BaseModel):
    source: str
    provider: str
    is_mock: bool
    is_realtime: bool
    as_of: datetime | None = None
    is_stale: bool
    warning: str | None = None

    @classmethod
    def mock_source(
        cls,
        *,
        provider: str,
        as_of: datetime | None = None,
        is_realtime: bool = False,
        warning: str | None = None,
    ) -> "DataStatus":
        return cls(
            source="mock",
            provider=provider,
            is_mock=True,
            is_realtime=is_realtime,
            as_of=as_of,
            is_stale=False,
            warning=warning or "Data is simulated and not suitable for investment decisions.",
        )

    @classmethod
    def live_source(
        cls,
        *,
        provider: str,
        as_of: datetime | None = None,
        is_realtime: bool = True,
        warning: str | None = None,
    ) -> "DataStatus":
        return cls(
            source="live",
            provider=provider,
            is_mock=False,
            is_realtime=is_realtime,
            as_of=as_of,
            is_stale=False,
            warning=warning,
        )

    @classmethod
    def stale_source(
        cls,
        *,
        provider: str,
        as_of: datetime | None,
        is_mock: bool = False,
        is_realtime: bool = False,
        warning: str | None = None,
    ) -> "DataStatus":
        return cls(
            source="stale",
            provider=provider,
            is_mock=is_mock,
            is_realtime=is_realtime,
            as_of=as_of,
            is_stale=True,
            warning=warning or "Data may be stale. Verify freshness before making decisions.",
        )

    @classmethod
    def unavailable_source(
        cls,
        *,
        provider: str,
        warning: str | None = None,
    ) -> "DataStatus":
        return cls(
            source="unavailable",
            provider=provider,
            is_mock=False,
            is_realtime=False,
            as_of=None,
            is_stale=True,
            warning=warning or "Data is unavailable from this provider.",
        )

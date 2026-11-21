from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class FlutterwaveObject(MutableMapping[str, Any]):
    """Dictionary-like object with attribute access for API responses.

    This deliberately mirrors Stripe's flexible resource-object idea: new fields returned by
    Flutterwave are preserved instead of being discarded by rigid models.
    """

    def __init__(self, values: Mapping[str, Any] | None = None) -> None:
        object.__setattr__(self, "_values", {})
        if values:
            for key, value in values.items():
                self._values[key] = self._convert(value)

    @classmethod
    def construct_from(cls, values: Mapping[str, Any] | None) -> "FlutterwaveObject":
        return cls(values or {})

    @classmethod
    def _convert(cls, value: Any) -> Any:
        if isinstance(value, Mapping):
            return FlutterwaveObject(value)
        if isinstance(value, list):
            return [cls._convert(item) for item in value]
        return value

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._values[key] = self._convert(value)

    def __delitem__(self, key: str) -> None:
        del self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self._values[name] = self._convert(value)

    def __repr__(self) -> str:
        return f"FlutterwaveObject({self._values!r})"

    def to_dict(self) -> dict[str, Any]:
        return {key: self._to_plain(value) for key, value in self._values.items()}

    @classmethod
    def _to_plain(cls, value: Any) -> Any:
        if isinstance(value, FlutterwaveObject):
            return value.to_dict()
        if isinstance(value, list):
            return [cls._to_plain(item) for item in value]
        return value


@dataclass(slots=True)
class FlutterwaveResponse:
    status: str | None
    message: str | None
    data: Any
    meta: FlutterwaveObject | None
    raw: dict[str, Any]
    http_status: int
    headers: Mapping[str, str]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        http_status: int,
        headers: Mapping[str, str],
    ) -> "FlutterwaveResponse":
        data = payload.get("data")
        converted_data = _convert_response_data(data)
        meta = payload.get("meta")
        return cls(
            status=None if payload.get("status") is None else str(payload.get("status")),
            message=None if payload.get("message") is None else str(payload.get("message")),
            data=converted_data,
            meta=FlutterwaveObject.construct_from(meta) if isinstance(meta, Mapping) else None,
            raw=dict(payload),
            http_status=http_status,
            headers=headers,
        )


def _convert_response_data(data: Any) -> Any:
    if isinstance(data, Mapping):
        return FlutterwaveObject.construct_from(data)
    if isinstance(data, list):
        return [FlutterwaveObject.construct_from(item) if isinstance(item, Mapping) else item for item in data]
    return data


class ListObject(Generic[T]):
    """List response with convenience helpers for page metadata.

    The SDK does not silently auto-fetch pages. Instead, `has_more` and `next_page` make
    pagination explicit and easy to test.
    """

    def __init__(
        self,
        *,
        data: list[T],
        meta: FlutterwaveObject | None,
        response: FlutterwaveResponse,
    ) -> None:
        self.data = data
        self.meta = meta
        self.response = response

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> T:
        return self.data[index]

    @property
    def page_info(self) -> FlutterwaveObject | None:
        if not self.meta:
            return None
        page_info = self.meta.get("page_info")
        return page_info if isinstance(page_info, FlutterwaveObject) else None

    @property
    def current_page(self) -> int | None:
        page_info = self.page_info
        value = None if page_info is None else page_info.get("current_page")
        return int(value) if value is not None else None

    @property
    def total_pages(self) -> int | None:
        page_info = self.page_info
        value = None if page_info is None else page_info.get("total_pages")
        return int(value) if value is not None else None

    @property
    def has_more(self) -> bool:
        if self.current_page is None or self.total_pages is None:
            return False
        return self.current_page < self.total_pages

    @property
    def next_page(self) -> int | None:
        if not self.has_more or self.current_page is None:
            return None
        return self.current_page + 1

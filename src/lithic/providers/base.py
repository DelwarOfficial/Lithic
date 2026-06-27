"""Provider protocol definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Return completion text for provider-formatted messages."""

    async def async_complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Async completion. Defaults to sync call in executor."""
        return self.complete(messages, **kwargs)

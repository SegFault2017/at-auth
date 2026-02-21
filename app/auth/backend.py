from dataclasses import dataclass
from typing import Protocol


@dataclass
class UserIdentity:
    provider_id: str
    email: str


class AuthBackend(Protocol):
    async def verify_token(self, token: str) -> UserIdentity: ...

import jwt
from jwt import PyJWKClient
from app.auth.backend import AuthBackend, UserIdentity


class ClerkAuthBackend:
    def __init__(self, jwks_url: str):
        self._jwks_client = PyJWKClient(jwks_url)

    async def verify_token(self, token: str) -> UserIdentity:
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return UserIdentity(
            provider_id=data["sub"],
            email=data.get("email", ""),
        )

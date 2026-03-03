import httpx
import jwt
from jwt import PyJWKClient

_jwks_clients: dict[str, PyJWKClient] = {}


def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(jwks_url, cache_jwk_set=True)
    return _jwks_clients[jwks_url]


async def verify_clerk_jwt(token: str, jwks_url: str) -> str | None:
    """Verify a Clerk session JWT and return the user_id (sub claim).

    Returns None if verification fails for any reason.
    """
    try:
        client = _get_jwks_client(jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload.get("sub")
    except (jwt.PyJWTError, Exception):
        return None

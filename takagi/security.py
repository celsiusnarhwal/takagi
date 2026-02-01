import json
import typing as t
from json import JSONDecodeError
from pathlib import Path

import pendulum

# noinspection PyUnresolvedReferences
from authlib.integrations.starlette_client import StarletteOAuth2App
from joserfc import jwe, jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import Token
from pydantic import validate_call

from takagi.serializable import TakagiAccessInfo, TakagiAccessToken
from takagi.settings import settings


@validate_call
def _get_key_file(key_type: t.Literal["RSA", "oct"]) -> Path:
    """
    Get the path to a key file.
    """
    file = (
        Path(__file__).parent / "data" / "keys" / f"{key_type.lower()}_private_key.json"
    )

    file.parent.mkdir(parents=True, exist_ok=True)

    return file


@validate_call
def _create_key(key_type: t.Literal["RSA", "oct"]) -> None:
    """
    Create a key.
    """
    if key_type == "RSA":
        size = 2048
        parameters = {"use": "sig", "alg": "RS256"}
    else:
        size = 256
        parameters = {"use": "enc", "alg": "A256GCM"}

    key = KeySet.generate_key_set(
        key_type, size, parameters=parameters, private=True, count=1
    )

    json.dump(key.as_dict(private=True), _get_key_file(key_type).open("w"))


@validate_call
def _get_key(key_type: t.Literal["RSA", "oct"]) -> KeySet:
    """
    Get a key, creating it if necessary.
    """
    key_file = _get_key_file(key_type)

    try:
        return KeySet.import_key_set(json.load(key_file.open()))
    except (FileNotFoundError, JSONDecodeError, JoseError):
        _create_key(key_type)
        return _get_key(key_type)


def get_rsa_key() -> KeySet:
    """
    Get the RSA key, creating it if necessary.
    """
    return settings().rsa_key or _get_key("RSA")


def get_oct_key() -> KeySet:
    """
    Get the octet sequence key, creating it if necessary.
    """
    return settings().oct_key or _get_key("oct")


def create_jwt(claims: dict) -> str:
    """
    Create a JWT.
    """
    return jwt.encode({"alg": "RS256"}, claims, get_rsa_key())


def decode_jwt(token: str, **claims: dict) -> Token:
    """
    Decode a JWT.
    """
    decoded = jwt.decode(token, get_jwks())
    jwt.JWTClaimsRegistry(**claims).validate(decoded.claims)

    return decoded


def create_jwe(data: str) -> str:
    """
    Create a JWE-encrypted string.
    """
    return jwe.encrypt_compact({"alg": "dir", "enc": "A256GCM"}, data, get_oct_key())


def decrypt_jwe(data: str) -> str:
    """
    Decrypt a JWE-encrypted string.
    """
    return jwe.decrypt_compact(data, get_oct_key()).plaintext.decode()


def get_jwks() -> KeySet:
    """
    Get the public JSON Web Key Set.
    """
    return KeySet.import_key_set(
        get_rsa_key().as_dict(private=False), parameters={"use": "sig"}
    )


async def create_tokens(
    *,
    github: StarletteOAuth2App,
    github_token: dict,
    scopes: list[str],
    oidc_metadata: dict,
    nonce: str | None = None,
) -> dict[str, str | int]:
    """
    Create a pair of access and ID tokens.
    """
    user_info = (
        (await github.get("/user", token=github_token)).raise_for_status().json()
    )

    now = pendulum.now("UTC")

    if settings().token_lifetime:
        expiry = now.add(seconds=settings().token_lifetime)
    else:
        # JWTs must have an expiry and Python only supports datetimes prior to the year 10000, so this is the closest
        # we can get to a token that never expires.
        expiry = pendulum.datetime(9999, 12, 31, 23, 23, 59, 999999, "UTC")

    identity_claims = {
        "iss": oidc_metadata["issuer"],
        "aud": github.client_id,
        "iat": now.int_timestamp,
        "exp": expiry.int_timestamp,
        "sub": str(user_info["id"]),
    }

    if "profile" in scopes:
        identity_claims.update(
            {
                "preferred_username": user_info["login"],
                "name": user_info["name"],
                "nickname": user_info["name"],
                "picture": user_info["avatar_url"],
                "profile": user_info["html_url"],
                "updated_at": pendulum.parse(user_info["updated_at"]).int_timestamp,
            }
        )

    if "email" in scopes and user_info.get("email"):
        identity_claims.update({"email": user_info["email"], "email_verified": True})

    if "groups" in scopes:
        organizations = (
            (await github.get("/user/orgs", token=github_token))
            .raise_for_status()
            .json()
        )

        if organizations:
            identity_claims["groups"] = [str(org["id"]) for org in organizations]

    if nonce is not None:
        identity_claims["nonce"] = nonce

    access_info = TakagiAccessInfo(
        token=github_token,
        scopes=scopes,
    )

    access_token = TakagiAccessToken(
        iss=oidc_metadata["issuer"],
        aud=oidc_metadata["userinfo_endpoint"],
        iat=now.int_timestamp,
        exp=expiry.int_timestamp,
        token=create_jwe(access_info.model_dump_json()),
    )

    tokens = {
        "access_token": access_token.to_jwt(),
        "token_type": "Bearer",
        "expires_at": expiry.int_timestamp,
        "id_token": create_jwt(identity_claims),
    }

    return tokens

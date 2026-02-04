import typing as t

import httpx

# noinspection PyUnresolvedReferences
from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.oauth2.rfc6749 import list_to_scope, scope_to_list
from fastapi import Request
from pydantic import BeforeValidator, validate_call
from starlette.datastructures import URL

from takagi.settings import settings


def get_oauth_client(**kwargs) -> StarletteOAuth2App:
    """
    Create a client for GitHub's OAuth2 API.
    """
    return OAuth().register(
        name="github",
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com",
        **kwargs,
    )


def get_httpx_client() -> httpx.AsyncClient:
    """
    Create an HTTPX client for GitHub's API.
    """
    return httpx.AsyncClient(base_url="https://api.github.com")


@validate_call
def convert_scopes(
    scopes: t.Annotated[list | tuple | set, BeforeValidator(scope_to_list)],
    *,
    to_format: t.Literal["openid", "github"],
    output_type: t.Literal[list, str],
) -> list | str:
    """
    Convert OpenID Connect scopes to GitHub scopes or vice versa.
    """
    scope_map = {"profile": "profile", "email": "user:email", "groups": "read:org"}

    if to_format == "openid":
        scope_map = {v: k for k, v in scope_map.items()}

    converter = scope_to_list if output_type is list else list_to_scope

    return converter([v for k, v in scope_map.items() if k in scopes])


def fix_redirect_uri(request: Request, redirect_uri: str | None) -> str | None:
    """
    Modify a redirect URI to be a subpath of the /r endpoint.
    """
    if redirect_uri is not None and not redirect_uri.startswith(
        f"{request.url_for('redirect')}/"
    ):
        redirect_uri = str(request.url_for("callback", redirect_uri=redirect_uri))

    return redirect_uri


def is_secure_transport(url: str | URL) -> bool:
    """
    Return `True` if the given URL is HTTPS or for a loopback address; `False` otherwise.
    """
    if not isinstance(url, URL):
        url = URL(url)

    return url.scheme == "https" or (
        settings().treat_loopback_as_secure
        and url.hostname in ["localhost", "127.0.0.1", "::1"]
    )


def client_is_allowed(client_id: int) -> bool:
    """
    Return `True` if the given client ID is allowed per `TAKAGI_ALLOWED_CLIENTS`; `False` otherwise.
    """
    return bool({client_id, "*"}.intersection(settings().allowed_clients))


def get_discovery_info(request: Request) -> dict:
    """
    Return OpenID Connect Discovery information.
    """
    return {
        "issuer": str(request.base_url),
        "authorization_endpoint": str(request.url_for("authorize")),
        "token_endpoint": str(request.url_for("token")),
        "revocation_endpoint": str(request.url_for("revoke")),
        "userinfo_endpoint": str(request.url_for("userinfo")),
        "introspection_endpoint": str(request.url_for("introspect")),
        "jwks_uri": str(request.url_for("jwks")),
        "claims_supported": [
            "sub",
            "preferred_username",
            "name",
            "nickname",
            "locale",
            "picture",
            "profile",
            "updated_at",
            "email",
            "email_verified",
            "groups",
        ],
        "grant_types_supported": ["authorization_code"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "scopes_supported": ["openid", "profile", "email", "groups"],
        "code_challenge_methods_supported": ["S256"],
        "service_documentation": "https://github.com/celsiusnarhwal/takagi",
    }

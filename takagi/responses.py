import typing as t

from pydantic import BaseModel, Field, HttpUrl


class TokenResponse(BaseModel, title="Token"):
    access_token: str
    token_type: t.Literal["Bearer"]
    expires_at: int = None
    id_token: str = Field(title="ID Token")


class UserInfoResponse(BaseModel, title="User Info"):
    sub: str = Field(
        title="Subject", description="The ID of the user's GitHub account."
    )
    preferred_username: str = Field(
        None, description="The username of the user's GitHub account."
    )
    name: str = Field(
        None, description="The display name of the user's GitHub account."
    )
    nickname: str = Field(None, description="Same as `name`.")
    picture: HttpUrl = Field(None, description="The URL of the user's GitHub avatar.")
    profile: HttpUrl = Field(None, description="The URL of the user's GitHub profile.")
    updated_at: int = Field(
        None,
        description="The [Unix time](https://en.wikipedia.org/wiki/Unix_time) "
        "at which the user's profile was last updated.",
    )
    email: str = Field(
        None,
        description="The primary email address associated with the user's GitHUb account.",
    )
    email_verified: bool = Field(
        None,
        description="Whether the primary email address associated with the user's GitHub account is verified.",
    )
    groups: list[str] = Field(
        None,
        description="A list of IDs of organizations the user is a member of and has granted your "
        "application access to. Each ID is prefixed with `org:`.",
    )


class IntrospectionResponse(BaseModel, title="Introspection"):
    active: bool = Field(description="Whether the access token is valid.")
    client_id: str = Field(
        None,
        title="Client ID",
        description="The client ID of the application the token was authorized for.",
    )
    username: str = Field(
        None,
        description="The GitHub username of the user associated with the access token.",
    )
    scope: str = Field(
        None,
        description="A space-separated list of scopes the access token was authorized with.",
    )
    sub: str = Field(
        None,
        title="Subject",
        description="The GitHub user ID of the user associated with the access token.",
    )
    iss: str = Field(None, title="Issuer", description="Same as `aud`.")
    aud: str = Field(
        None,
        title="Audience",
        description="The URL at which Takagi was accessed when the access token was authorized.",
    )
    iat: int = Field(
        None,
        title="Issued At",
        description="The [Unix time](https://en.wikipedia.org/wiki/Unix_time) at which the access token was issued.",
    )
    exp: int = Field(
        None,
        title="Expires At",
        description="The [Unix time](https://en.wikipedia.org/wiki/Unix_time) at which the access token expires.",
    )


class JWKSResponse(BaseModel, title="JSON Web Key Set"):
    class JWK(BaseModel, title="JSON Web Key"):
        n: str = Field(title="Modulus")
        e: str = Field(title="Exponent")
        kty: t.Literal["RSA"] = Field(title="Key Type")
        kid: str = Field(title="Key ID")
        use: t.Literal["sig"] = Field(title="Public Key Use")

    keys: list[JWK]


class WebFingerResponse(BaseModel, title="JSON Resource Descriptor"):
    class WebFingerLink(BaseModel, title="Link"):
        rel: t.Literal["http://openid.net/specs/connect/1.0/issuer"] = Field(
            title="Link Relation"
        )
        href: HttpUrl = Field(title="Target URI")

    subject: str
    links: list[WebFingerLink]


class DiscoveryResponse(BaseModel, title="OpenID Connect Discovery"):
    issuer: HttpUrl
    authorization_endpoint: HttpUrl
    token_endpoint: HttpUrl
    userinfo_endpoint: HttpUrl = Field(title="User Info Endpoint")
    revocation_endpoint: HttpUrl
    introspection_endpoint: HttpUrl
    jwks_uri: HttpUrl = Field(title="JWKS URI")
    claims_supported: list[str]
    grant_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str] = Field(
        title="ID Token Signing Alg Values Supported"
    )
    token_endpoint_auth_methods_supported: list[str]
    response_types_supported: list[str]
    scopes_supported: list[str]


class HTTPClientErrorResponse(BaseModel, title="HTTP Client Error"):
    detail: str | dict

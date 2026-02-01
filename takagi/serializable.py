import secrets
import time
import typing as t

from authlib.oauth2.rfc6749 import MismatchingStateException
from fastapi.exceptions import HTTPException
from joserfc.errors import JoseError
from pydantic import BaseModel, ValidationError, computed_field

from takagi import security


class JWT(BaseModel):
    @computed_field
    @property
    def randomizer(self) -> str:
        return secrets.token_urlsafe(32)

    def to_jwt(self) -> str:
        """
        Serialize this model to a JWT.
        """
        return security.create_jwt(self.model_dump())

    @classmethod
    def from_jwt(cls, token: str, **claims) -> t.Self:
        """
        Deserialize this model from a JWT.
        """
        decoded = security.decode_jwt(token, **claims)
        return cls.model_validate(decoded.claims)


class TakagiStateData(JWT):
    redirect_uri: str | None
    state: str | None
    nonce: str | None
    scopes: list[str] | None
    referrer: str | None

    @computed_field
    @property
    def iat(self) -> int:
        return int(time.time())

    @computed_field
    @property
    def exp(self) -> int:
        return self.iat + 300

    @classmethod
    def from_jwt(cls, token: str, **claims: dict) -> t.Self:
        try:
            return super(TakagiStateData, cls).from_jwt(token, **claims)
        except (JoseError, ValidationError):
            raise MismatchingStateException()


class TakagiAuthorizationData(JWT):
    code: str
    redirect_uri: str | None
    nonce: str | None
    scopes: list[str] | None

    @computed_field
    @property
    def iat(self) -> int:
        return int(time.time())

    @computed_field
    @property
    def exp(self) -> int:
        return self.iat + 300

    @classmethod
    def from_jwt(cls, token: str, **claims: dict) -> t.Self:
        try:
            return super(TakagiAuthorizationData, cls).from_jwt(token, **claims)
        except (JoseError, ValidationError):
            raise HTTPException(400, "Invalid authorization code")


class TakagiAccessInfo(BaseModel):
    token: dict
    client_id: str
    client_secret: str
    scopes: list[str]


class TakagiAccessToken(JWT):
    iss: str
    aud: str
    iat: int
    exp: int
    token: str

    @property
    def access_info(self) -> TakagiAccessInfo:
        decrypted = security.decrypt_jwe(self.token)
        return TakagiAccessInfo.model_validate_json(decrypted)

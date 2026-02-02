import json
import logging
import typing as t
from functools import lru_cache
from pathlib import Path

import dns.name
import durationpy
from joserfc.jwk import KeySet, OctKey, RSAKey
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    TypeAdapter,
    field_validator,
)
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import (
    BaseSettings,
    NoDecode,
    SettingsConfigDict,
)

Duration = t.Annotated[
    int, BeforeValidator(lambda v: durationpy.from_str(v).total_seconds())
]


class TakagiPrivateSettings(BaseModel):
    show_scalar_devtools_on_localhost: bool = False


class TakagiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TAKAGI_", env_ignore_empty=True, env_nested_delimiter="__"
    )

    allowed_hosts: t.Annotated[list[str], NoDecode] = Field(default_factory=list)
    allowed_clients: t.Annotated[list[str], NoDecode] = Field(
        default=["*"], validate_default=False
    )
    base_path: str = "/"
    fix_redirect_uris: bool = False
    token_lifetime: Duration = Field(None, ge=60, validate_default=False)
    root_redirect: t.Literal["repo", "settings", "docs", "off"] = "repo"
    treat_loopback_as_secure: bool = True
    return_to_referrer: bool = False
    allowed_webfinger_hosts: t.Annotated[list[dns.name.Name], NoDecode] = Field(
        default_factory=list, validate_default=False
    )
    keyset: t.Annotated[KeySet, NoDecode] = Field(None, validate_default=False)
    enable_docs: bool = True

    private: TakagiPrivateSettings = Field(default_factory=TakagiPrivateSettings)

    @property
    def rsa_key(self) -> KeySet:
        if not self.keyset:
            return None

        return KeySet([(next(key for key in self.keyset if isinstance(key, RSAKey)))])

    @property
    def oct_key(self) -> KeySet:
        if not self.keyset:
            return None

        return KeySet([next((key for key in self.keyset if isinstance(key, OctKey)))])

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def validate_allowed_hosts(cls, v: str | list) -> list[str]:
        hosts = v.split(",") if isinstance(v, str) else v

        if "*" in hosts:
            logging.getLogger("uvicorn").warning(
                "Setting TAKAGI_ALLOWED_HOSTS to '*' is insecure and not recommended."
            )

        return hosts + ["localhost", "127.0.0.1", "::1"]

    @field_validator("allowed_clients", mode="before")
    @classmethod
    def validate_allowed_clients(cls, v: str) -> list[str]:
        return v.split(",")

    @field_validator("allowed_webfinger_hosts", mode="before")
    @classmethod
    def validate_allowed_webfinger_hosts(cls, v: str) -> list[dns.name.Name]:
        hosts = []

        for i in v.split(","):
            name = dns.name.from_text(i)

            if name.is_wild() and len(name) < 3:
                raise ValueError(
                    "The unqualified wildcard ('*') is not permitted in TAKAGI_ALLOWED_WEBFINGER_HOSTS"
                )

            hosts.append(name)

        return hosts

    @field_validator("keyset", mode="before")
    @classmethod
    def validate_keyset(cls, v: str) -> KeySet:
        try:
            keyset_dict = json.loads(v)
        except json.JSONDecodeError:
            keyset_file = TypeAdapter(Path).validate_python(v)

            if not keyset_file.is_absolute():
                raise ValueError("If TAKAGI_KEYSET is a path, it must be absolute")

            if str(keyset_file.resolve()).startswith(str(Path(__file__).parent)):
                raise ValueError(
                    "If TAKAGI_KEYSET is a path, it cannot be located within /app/takagi"
                )

            try:
                keyset_dict = json.load(keyset_file.open())
            except Exception as e:
                raise ValueError(e.args)

        keyset = KeySet.import_key_set(keyset_dict)

        if len(keyset.keys) != 2:
            raise ValueError("A custom private keyset must contain exactly two keys")

        try:
            rsa_key = next(key for key in keyset if isinstance(key, RSAKey))
        except StopIteration:
            raise ValueError("A custom private keyset must contain an RSA key")

        try:
            oct_key = next(key for key in keyset if isinstance(key, OctKey))
        except StopIteration:
            raise ValueError(
                "A custom private keyset must contain an octet sequence key"
            )

        if rsa_key.alg != "RS256":
            raise ValueError(
                "The RSA key in a custom private keyset must be an RS256 key"
            )

        if rsa_key.get("use") != "sig":
            raise ValueError(
                "The RSA key in a custom private keyset must explicitly support signing"
            )

        if not rsa_key.is_private:
            raise ValueError(
                "The RSA key in a custom private keyset must be a private key"
            )

        if oct_key.alg != "A256GCM":
            raise ValueError(
                "The octet sequence key in a custom private keyset must be an A256GCM key"
            )

        if oct_key.get("use") != "enc":
            raise ValueError(
                "The octet sequence key in a custom private keyset must explicitly support encryption"
            )

        logging.getLogger("uvicorn").info("Takagi is using a custom private keyset.")

        return keyset

    @field_validator("enable_docs")
    @classmethod
    def validate_enable_docs(cls, v: bool, info: ValidationInfo) -> bool:
        return v or info.data["root_redirect"] == "docs"


@lru_cache
def settings() -> TakagiSettings:
    return TakagiSettings()


settings()

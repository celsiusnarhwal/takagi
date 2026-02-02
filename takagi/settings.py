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
    keyset_file: Path = Field(None, validate_default=False)
    keyset: t.Annotated[KeySet, NoDecode] | None = Field(None)
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

    @field_validator("keyset_file")
    @classmethod
    def validate_keyset_file(cls, v: Path) -> Path:
        variable_name = "TAKAGI_KEYSET_FILE"

        if not v.is_absolute():
            raise ValueError(f"{variable_name} must be a absolute path")

        v = v.resolve()

        if str(v).startswith((str(Path(__file__).parent.resolve()))):
            raise ValueError("TAKAGI_KEYSET_FILE cannot be located within /app/takagi")

        KeySet.import_key_set(json.load(v.open()))
        return v

    @field_validator("keyset", mode="before")
    @classmethod
    def validate_keyset(cls, v: str, info: ValidationInfo) -> KeySet:
        if keyset_file := info.data.get("keyset_file"):
            if v is not None:
                raise ValueError(
                    "You cannot provide both TAKAGI_KEYSET and TAKAGI_KEYSET_FILE"
                )

            keyset = KeySet.import_key_set(json.load(keyset_file.open()))
        elif v is None:
            return v
        else:
            keyset = KeySet.import_key_set(json.loads(v))

        if len(keyset.keys) != 2:
            raise ValueError("Custom private keysets must contain exactly two keys")

        try:
            rsa_key = next(key for key in keyset if isinstance(key, RSAKey))
        except StopIteration:
            raise ValueError("Custom private keysets must contain an RSA key")

        try:
            oct_key = next(key for key in keyset if isinstance(key, OctKey))
        except StopIteration:
            raise ValueError(
                "Custom private keysets must contain an octet sequence key"
            )

        if rsa_key.alg != "RS256":
            raise ValueError(
                "The RSA key in a custom private keyset must be an RS256 key"
            )

        if rsa_key.check_use("sig") is not None:
            raise ValueError(
                "The RSA key in a custom private keyset must support signing"
            )

        if not rsa_key.is_private:
            raise ValueError(
                "The RSA key in custom private keyset must be a private key"
            )

        if oct_key.alg != "A256GCM":
            raise ValueError(
                "The octet seqeunce key in custom private keyset must be an A256GCM key"
            )

        if oct_key.check_use("enc") is not None:
            raise ValueError(
                "The octet sequence key in a custom private keyset must support encryption"
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

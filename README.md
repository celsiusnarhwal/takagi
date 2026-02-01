# Takagi

Takagi enables you to use [GitHub](https://github.com) as
an [OpenID Connect](https://auth0.com/docs/authenticate/protocols/openid-connect-protocol) (OIDC) provider. With it, you
can use GitHub to identify your application's users without needing to implement specific support for GitHub's OAuth2
API.

Takagi is a sister project to [Snowflake](https://github.com/celsiusnarhwal/snowflake), which does the same thing
but for Discord. You should check that out, too.

> [!important]
> Takagi requires HTTPS for external connections. (By default, HTTP connections on `localhost` are fine; see
> [Configuration](#configuration).)

## Installation

[Docker](https://docs.docker.com/get-started) is the only supported way of running Takagi. You will almost always 
want to set the `TAKAGI_ALLOWED_HOSTS` environment variable; see [Configuration](#configuration).

> [!note]
> Throughout this README, `takagi.example.com` will be used as a placeholder for the domain at which your
> Takagi instace is reachable.

<hr>

<details>
<summary>Supported tags</summary>
<br>

| **Name**             | **Description**                                                                            | **Example**                                                                      |
|----------------------|--------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| `latest`             | The latest stable version of Takagi.                                                       | `ghcr.io/celsiusnarhwal/takagi:latest`                                           |
| Major version number | The latest release of this major version of Takagi. May be optionally prefixed with a `v`. | `ghcr.io/celsiusnarhwal/takagi:1`<br/>`ghcr.io/celsiusnarhwal/takagi:v1`         |
| Minor version number | The latest release of this minor version of Takagi. May be optionally prefixed with a `v`. | `ghcr.io/celsiusnarhwal/takagi:1.0`<br/>`ghcr.io/celsiusnarhwal/takagi:v1.0`     |
| Exact version number | This version of Takagi exactly. May be optionally prefixed with a `v`.                     | `ghcr.io/celsiusnarhwal/takagi:1.0.0`<br/>`ghcr.io/celsiusnarhwal/takagi:v1.0.0` |
| `edge`               | The latest commit to Takagi's `main` branch. Unstable.                                     | `ghcr.io/celsiusnarhwal/takagi:edge`                                             |

</details>

<hr>

### Docker Compose

```yaml
services:
  takagi:
    image: ghcr.io/celsiusnarhwal/takagi:latest
    container_name: takagi
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - TAKAGI_ALLOWED_HOSTS=takagi.example.com
    volumes:
      - /some/directory/on/your/machine:/app/takagi/data
```

### Docker CLI

```shell
docker run --name takagi \
--restart unless-stopped \
-p "8000:8000" \
-e "TAKAGI_ALLOWED_HOSTS=takagi.example.com"
-v "/some/directory/on/your/machine:/app/takagi/data" \
ghcr.io/celsiusnarhwal/takagi:latest
```

## Usage

First, [create an OAuth application in your GitHub developer settings](https://github.com/settings/applications/new). 
Put in whatever you want for the application name and homepage URL.

For the **authorization callback URL**, you must set it to `https://takagi.example.com/r/{YOUR_REDIRECT_URI}`,
where `{YOUR_REDIRECT_URI}` is the actual intended redirect URI for your application. For example, a redirect
URI of `https://myapp.example.com/callback` would be set as as 
`https://takagi.example.com/r/https://myapp.example.com/callback`.

> [!tip]
> If you're unable to control the redirect URI your OIDC client provides to Takagi, set
> the `TAKAGI_FIX_REDIRECT_URIS` environment variable to `true`. See [Configuration](#configuration)
> for details.

From there, Takagi works just like any other OIDC provider. Your app redirects to Takagi for authorization;
upon succcessful authorization, Takagi provides your app with an authorization code, which your app returns
to Takagi in exchange for an access token and an ID token. The access token can be sent to Takagi's
`/userinfo` endpoint to obtain the associated identity claims, or your application can decode the ID token
directly to obtain the same claims.

Frankly, if you're reading this then you should already know how this works.

## OIDC Information

### Endpoints

| **Endpoint**                    | **Path**                            |
|---------------------------------|-------------------------------------|
| Authorization                   | `/authorize`                        |
| Token                           | `/token`                            |
| User Info                       | `/userinfo`                         |
| JSON Web Key Set                | `/.well-known/jwks.json`            |
| OIDC Discovery                  | `/.well-known/openid-configuration` |
| [WebFinger](#webfinger-support) | `/.well-known/webfinger`            |

### Supported Scopes

| **Scope** | **Requests**                                                                                     | **Required?** |
|-----------|--------------------------------------------------------------------------------------------------|---------------|
| `openid`  | To authenticate using OpenID Connect.                                                            | Yes           |
| `profile` | Basic information about the user's GitHub account.                                               | No            |
| `email`   | The email address associated with the user's GitHub account and whether or not it is verified.   | No            |
| `groups`  | A list of IDs of organizations the user is a member of and has made visible to your application. | No            |

### Supported Claims

> [!important]
> By default, tokens issued by Takagi do not expire.[^1] This mirrors the behavior of GitHub OAuth2 access tokens, which
> also do not expire. If you would like Takagi-issued tokens to expire, set the `TAKAGI_TOKEN_LIFETIME`
> environment variable (see [Configuration](#configuration)).

#### ID Tokens

Depending on the provided scopes, Takagi-issued ID tokens include some subset of the following claims:

| **Claim**            | **Description**                                                                                                                                                                                                    | **Required Scopes (in addition to `openid`)** |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| `iss`                | The URL at which the client accessed Takagi.                                                                                                                                                                       | None                                          |
| `sub`                | The ID of the user's GitHub account.                                                                                                                                                                               | None                                          |
| `aud`                | The client ID of your GitHub application.                                                                                                                                                                          | None                                          |
| `iat`                | The [Unix time](https://en.wikipedia.org/wiki/Unix_time) at which the token was issued.                                                                                                                            | None                                          |
| `exp`                | The [Unix time](https://en.wikipedia.org/wiki/Unix_time) past which the token should be considered expired and thus no longer valid.                                                                               | None                                          |
| `preferred_username` | The username of the user's GitHub account.                                                                                                                                                                         | `profile`                                     |
| `name`               | The display name of the user's GitHub account.                                                                                                                                                                     | `profile`                                     |
| `nickname`           | Same as `name`.                                                                                                                                                                                                    | `profile`                                     |
| `picture`            | The URL of the avatar of the user's GitHub account.                                                                                                                                                                | `profile`                                     |
| `profile`            | The URL of the user's GitHub profile.                                                                                                                                                                              | `profile`                                     |
| `updated_at`         | The [Unix time](https://en.wikipedia.org/wiki/Unix_time) at which the user's profile information was last updated.                                                                                                 | `profile`                                     |
| `email`              | The pubilc email address associated with the user's GitHub profile. If the user has not set a public email address, this claim will not be present.                                                                | `email`                                       |
| `email_verified`     | Whether the email address associated with the user's GitHub account is verified.                                                                                                                                   | `email`                                       |
| `groups`             | A list of IDs of organizations the user is a member of and has authorized your application to access. If the user does not authorize your application to access any organizations, this claim will not be present. | `groups`                                      |
| `nonce`              | If the `nonce` parameter was sent to the authorization endpoint, this claim will contain its value.                                                                                                                | None                                          |

#### Access Tokens

Takagi-issued access tokens include the following claims:


| **Claim** | **Description**                                                                                                                      | **Required Scopes (in addition to `openid`)** |
|-----------|--------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| `iss`     | The URL at which the client accessed Takagi.                                                                                         | None                                          |
| `sub`     | The ID of the user's GitHub account.                                                                                                 | None                                          |
| `aud`     | The URL of Takagi's `/userinfo` endpoint.                                                                                            | None                                          |
| `iat`     | The [Unix time](https://en.wikipedia.org/wiki/Unix_time) at which the token was issued.                                              | None                                          |
| `exp`     | The [Unix time](https://en.wikipedia.org/wiki/Unix_time) past which the token should be considered expired and thus no longer valid. | None                                          |
| `token`   | The OAuth2 access token granted by GitHub. This token is encrypted and only usable by Takagi.                                        | None                                          |


#### User Info

The `/userinfo` endpoint returns the same claims as ID tokens but does not include `iss`, `aud`,
`iat`, `exp`, or `nonce`.

### PKCE Support

For applications that cannot securely store a client secret, Takagi supports the
[PKCE-enhanced authorization code flow](https://datatracker.ietf.org/doc/html/rfc7636).
Make sure the `Public Client` option is enabled in your GitHub application's OAuth2 settings.

### WebFinger Support

Takagi provides a [WebFinger](https://en.wikipedia.org/wiki/WebFinger) endpoint at `/.well-known/webfinger`
to enable the discovery of Takagi as the OIDC provider for email addresses at domains permitted by the
`TAKAGI_ALLOWED_WEBFINGER_HOSTS` environment variable (see [Configuration](#configuration)). The endpoint
only supports `acct:` URIs containing email addresses and does not support any link relations other than OpenID Connnect.

The endpoint will return an HTTP 404 error for email addresses at non-whitelisted domains.

## HTTPS and Reverse Proxies

As previously mentioned, Takagi requires HTTPS for external connections. If you're serving Takagi
behind a reverse proxy and connecting to the reverse proxy over HTTPS, you will likely need to configure
[Uvicorn](https://www.uvicorn.org) — which Takagi uses under the hood — to trust the IP address
of your reverse proxy.

You can do this by setting the `UVICORN_FORWARDED_ALLOW_IPS` environment variable to a comma-separated list of IP
addresses or networks, at least one of which must match the IP of your reverse proxy. You can also set it to `*` to
trust all IP addresses, but this is generally not recommended.

For more information, see [Uvicorn's documentation](https://www.uvicorn.org/deployment/#proxies-and-forwarded-headers).

## Custom Private Keys

> [!note]
> This is an advanced feature most users won't need.

By default, Takagi writes its private keys to `/app/takagi/data`, which you are instructed to mount on your host machine 
(see [Installation](#installation)). As an alternative to this, Takagi allows you to provide your own private keys via the 
`TAKAGI_KEYSET` environment variable. This may be useful, for example, in environments where mounting 
`/app/takagi/data` isn't possible, or if you'd just prefer to keep the private keys in an environment variable rather 
than have them persisted to the disk.

Takagi provides a command to generate private keys:

```shell
docker run ghcr.io/celsiusnarhwal/takagi keygen
```

The output of this command can be supplied to `TAKAGI_KEYSET` as-is.

It's possible to compose a value for the variable yourself, but there are several strict requirements.
I recommend you use the command instead.

<details>
<summary>For reference, a suitable value for the variable looks like this (click to expand):</summary>
<br/>

```json5
// For demonstration purposes only, do not actually use this keyset. Obviously.
{
  "keys": [
    {
      "n": "1PZYs3MrRkF83qVCoZ1qEJ3doCWaOflTVaZNceqYx4F1m_p_prUlzpBlsIky0q45e4ov3hehSh3FkvlnXLzYrD_Ewgwjy7xwIEhR7zyUUYMlUSCdb0Bq8mFRVG0zPYOSAY3CFkadnH0vwroJJcnc_mmAssfu6eUaIB7kfnqFx2RI3jXzi-runGrki8Y2yVAjovlgulX04Y0GD60kt1-vwva8Goci8Rij0IIna4GyKjYwxzKrOvMqI9_td7JJItF4QiDMd_SSjf8p6TenaWG26gb0vWhkzR6zWs-lVxMJYFkhnrGRk9urq6Zk4r_mmez7NPIyYAS5GWUW_Of7c-_h6w",
      "e": "AQAB",
      "d": "DK-gGRCDQ2wjRCAUGAyIhPTifue-iDWSAUgm1OJkt32-w8voTsX7upJffGSv4lz-j51rvI8rzH55hofU4HFfduNVlTmj6D8RbtrgBqBVNYXaczq-JiJwPIAPmDfpFYEA8ZbAORN70BalAbSTVuzvfThLslq2oLhFFiTA98fUsEvtN0O_FwNgvzJGfwvVGEmP6grYjqQr0NSqpD3tj2fq2AC5531ri1fjPyDE9wvQM4_EkZ0eOHtJW7ztfimiv_pgz1B_V6p26_FMhzhKkBepyMIewGPY4mzP-v4zlQILL6uYP9IbOZf1bCGjgcPF5lxQkL9Hjq1z0bRrpQgkoowAAQ",
      "p": "79NHLDfiFlo-lml4yVRVrRbrFZknbO506NdB-JKNcs1H7uYf_UTiY0E-oScvTZdgti0lxWh8syUCmXhkqLykrGgHG1M7uSmGACki35_diG5VTyIJuO4g92lLjw6d0slBcqaLZyeWctC_gU8F262HX97BombfIM6Nb2pWQ7zAQ-s",
      "q": "41NDWHVyTZkOjgwd8WIuYmBVd59MRYXyo_sBFkku8WyH21q-B7iTuMFcb7i61e0Qv8HPAchljqqEl3d91DpMOFTEy-MHoV2jn7_D4Grxsqb6mNomdOcC0oN4o7ZAvdJzffVfJXWBFwNbXyg7o3Byyr4Rl3OSi8HonYKVR80tWgE",
      "dp": "7SK6Q2zWb0e4jz2nI1vyg34f4XFY3ItEql7-am1u089Li1uc0e_k8kO3S93VFiHSjRBDQtk4RGMaGOpEjdxJ7_fE3y4D5ei7CTmjs_79LEP8soxzlJpRmpJRFhlb0OsTfexT9yHbz5e9ZHzgzADf1NoMGSsjAet7SmmY9s2SRxU",
      "dq": "2XJO7DHD-agbvRKoHbqdxeqCNp_BFIuxctvpyUiNx8_aEKA3QCl13HfRlOiuh21x5QtdmUX4p0RC-qQJT9XIDOZBLQpoxRlOJ8QGeQezVQHWmhmqSY6kK3wpDOiL-0dwxB7POYSxy7KhV1-j1I3-sCKpryaVGmyMtwYvB3SjGgE",
      "qi": "gYDgAbG3OHiQzLF76WuVfOoS2yUc_wJEExTvAYaRZ-yPEQBk4b3J5rYZUmxGJUMVzrNBEfMKR0bXwFB76JR53jD_NEOBUseTd4E4YldX_CMrw2XaopE4ftuR-5EklaOP2jP6Zqr3QQpqKpO9G-nC8ZQY5Gz4DWEtz4v0gUvvV_I",
      "use": "sig",
      "alg": "RS256",
      "kty": "RSA",
      "kid": "D-byh_ZgjoJOOho7vui-P_7WENzRKxgUAgiHZJOcHig"
    },
    {
      "k": "9AY2hzl0Sje9Zwv_XNHuz1BdEESmkVplMvap4KGfIeI",
      "use": "enc",
      "alg": "A256GCM",
      "kty": "oct",
      "kid": "GtMvEe77qYhPK6sOkWjuU9Yynzv-u8WYLCdwXN-qkGA"
    }
  ]
}
```

</details>

If `TAKAGI_KEYSET` is set, there's no need to mount `/app/takagi/data`. On startup, Takagi
will log a message affirming that a custom private keyset is in use.

## Configuration

Takagi is configurable through the following environment variables (all optional):

| **Environment Variable**          | **Type** | **Description**                                                                                                                                                                                                                                                                                                                                                                          | **Default**               |
|-----------------------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| `TAKAGI_ALLOWED_HOSTS`            | String   | A comma-separated list of hostnames at which Takagi may be accessed. Wildcard domains (e.g., `*.example.com`) and IP addresses are supported. You can also set this to `*` to allow all hostnames, but this is not recommended.<br/><br/>Loopback addresses (e.g., `localhost`) are always included.                                                                                     | `localhost,127.0.0.1,::1` |
| `TAKAGI_ALLOWED_CLIENTS`          | String   | A comma-separated list of GitHub application client IDs. Takagi will only fulfill authorization requests for client IDs in this list.<br/><br/>This can be set to `*` to allow all client IDs.                                                                                                                                                                                           | `*`                       |
| `TAKAGI_BASE_PATH`                | String   | The URL path at which Takagi is being served. This may be useful if you're serving Takagi behind a reverse proxy.                                                                                                                                                                                                                                                                        | `/`                       |
| `TAKAGI_FIX_REDIRECT_URIS`        | Boolean  | Whether to automatically correct redirect URIs to subpaths of Takagi's `/r` endpoint as necessary. This may be useful for OIDC clients that don't allow you to set the redirect URI they use.<br/><br/>The redirect URIs you set in the GitHub Developer Portal must always be subpaths of `/r` regardless of this setting.                                                              | `false`                   |                                                                                                                                                                                                                                                                                                                                   |               |              |
| `TAKAGI_TOKEN_LIFETIME`           | String   | A [Go duration string](https://pkg.go.dev/time#ParseDuration) representing the amount of time after which Takagi-issued tokens should expire. In addition to the standard Go units, you can use `d` for day, `w` for week, `mm` for month, and `y` for year.[^2]<br/><br/>Must be greater than or equal to 60 seconds.                                                                   | N/A                       |
| `TAKAGI_ROOT_REDIRECT`            | String   | Where Takagi's root path redirects to. Must be `repo`, `settings`, `docs`, or `off`.<br/><br/>`repo` redirects to Takagi's GitHub repository; `settings` redirects to the user's GitHub account settings; `docs` redirects to Takagi's interactive API documentation; `off` responds with an HTTP 404 error.<br/><br/>Setting this to `docs` will force `TAKAGI_ENABLE_DOCS` to be true. | `repo`                    |
| `TAKAGI_TREAT_LOOPBACK_AS_SECURE` | Boolean  | Whether Takagi will consider loopback addresses (e.g., `localhost`) to be secure even if they don't use HTTPS.                                                                                                                                                                                                                                                                           | `true`                    |
| `TAKAGI_RETURN_TO_REFERRER`       | Boolean  | If this is `true` and the user denies an authorization request, Takagi will redirect the user back to the initiating URL.[^4] Otherwise, Takagi behaves according to [OpenID Connect Core 1.0 § 3.1.2.6](https://openid.net/specs/openid-connect-core-1_0.html#AuthError).                                                                                                               | `false`                   |
| `TAKAGI_ALLOWED_WEBFINGER_HOSTS`  | String   | A comma-separated lists of domains allowed in `acct:` URIs sent to Takagi's WebFinger endpoint. The endpoint will return an HTTP 404 error for URIs with domains not permitted by this setting.<br/><br/> Wildcard domains (e.g., `*.example.com`) are supported, but the unqualified wildcard (`*`) is not.                                                                             | N/A                       |
| `TAKAGI_KEYSET`                   | String   | See [Custom Private Keys](#custom-private-keys).                                                                                                                                                                                                                                                                                                                                         | N/A                       |
| `TAKAGI_ENABLE_DOCS`              | Boolean  | Whether to serve Takagi's interactive API documentation at `/docs`. This also controls whether Takagi's [OpenAPI](https://spec.openapis.org/oas/latest.html) schema is served at `/openapi.json`.<br/><br/>This is forced to be `true` if `TAKAGI_ROOT_REDIRECT` is set to `docs`.                                                                                                       | `false`                   |

<br>

Uvicorn will respect most[^3] of [its own environment variables](https://www.uvicorn.org/settings/) if they are set, but `UVICORN_FORWARDED_ALLOW_IPS` is the only one supported by Takagi. Please don't open an issue if you set any of the others and something breaks.

[^1]: Technically, they expire on December 31st, 9999 at 23:23:59.999999 UTC, but you will die long before then so don't worry about it.

[^2]: 1 day = 24 hours, 1 week = 7 days, 1 month = 30 days, and 1 year = 365 days.

[^3]: With the exceptions of `UVICORN_HOST` and `UVICORN_PORT`.

[^4]: Specifically, if the 
[`Referer` header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referer) was sent to the 
authorization endpoint and the callback endpoint recieves an `error` parameter with a value of `access_denied`, 
Takagi will redirect to the URL that was given by `Referer` at the authorization endpoint.


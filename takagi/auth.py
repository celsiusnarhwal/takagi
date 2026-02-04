from fastapi.security import HTTPBasic, HTTPBearer


class ClientCredentials(HTTPBasic):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            {
                "scheme_name": "Client Credentials",
                "description": "The GitHub application's client ID (username) and client secret (password).",
            }
        )

        super().__init__(*args, **kwargs)


class AccessToken(HTTPBearer):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            {
                "scheme_name": "Access Token",
                "description": "An access token recieved from the `/token` endpoint.",
            }
        )

        super().__init__(*args, **kwargs)

import json

from joserfc.jwk import KeySet, OctKey, RSAKey


def keygen():
    rsa_key = RSAKey.generate_key(
        2048, parameters={"use": "sig", "alg": "RS256"}, private=True
    )

    oct_key = OctKey.generate_key(
        256, parameters={"use": "enc", "alg": "A256GCM"}, private=True
    )

    keyset = KeySet([rsa_key, oct_key])

    print(json.dumps(keyset.as_dict(private=True)))

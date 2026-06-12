from __future__ import annotations

import base64
import os
from typing import Any

from gmssl import sm2

SM2_PUBLIC_KEY = (
    "04bdc8610f8a2c561b5112301dd869c5c56370e5da13f37781c98679e5710d1d"
    "9a96d3d3882c1fe0149c5b16a99e290632b23eaaed18aecc4e3d358ac2baa10062"
)

RSA_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCbLIEre5wiSriqqxRb1fPsdgB0
EBNrNUu8Cq+uFDntMI9YvMcNScKym1E582yNK9K0v4pacCQ4U5+OqcmagLrj6pBqN
o/yy7RdMVy2bQdDsvkgJovK6Rz+iiw/Raqrhkl052Z+4iieQkbSXOKeXPX/610SE
ynqg07YCZXmJT2M2QIDAQAB
-----END PUBLIC KEY-----
"""


def qhp_base64(value: Any) -> str:
    return base64.b64encode(str(value).encode("utf-8")).decode("ascii")


def sm2_sign_payload(payload: dict[str, Any]) -> str:
    plain = _assemble_payload(payload)
    encoded_plain = base64.b64encode(plain.encode("utf-8"))
    crypt = sm2.CryptSM2(public_key=SM2_PUBLIC_KEY[2:], private_key="", mode=0)
    return "04" + crypt.encrypt(encoded_plain).hex()


def rsa_encrypt_path(path: str) -> str:
    modulus, exponent = _load_rsa_public_numbers(RSA_PUBLIC_KEY_PEM)
    key_size = (modulus.bit_length() + 7) // 8
    message = path.encode("utf-8")
    if len(message) > key_size - 11:
        raise ValueError("Message too long for RSA PKCS#1 v1.5 encryption")
    padding_length = key_size - len(message) - 3
    padding_bytes = bytearray()
    while len(padding_bytes) < padding_length:
        candidate = os.urandom(padding_length - len(padding_bytes))
        padding_bytes.extend(byte for byte in candidate if byte != 0)
    encoded_message = b"\x00\x02" + bytes(padding_bytes[:padding_length]) + b"\x00" + message
    encrypted_int = pow(int.from_bytes(encoded_message, "big"), exponent, modulus)
    encrypted = encrypted_int.to_bytes(key_size, "big")
    return base64.b64encode(encrypted).decode("ascii")


def encode_request_payload(payload: dict[str, Any], *, sign: bool = True) -> dict[str, str]:
    encoded = {key: qhp_base64(value) for key, value in payload.items() if value not in (None, "")}
    if sign:
        encoded["sign"] = sm2_sign_payload(payload)
    return encoded


def _assemble_payload(payload: dict[str, Any]) -> str:
    parts = []
    for key in sorted(payload):
        value = payload[key]
        if key == "sign" or key == "" or value in (None, ""):
            continue
        parts.append(f"{key}={value}")
    return "&".join(parts)


def _load_rsa_public_numbers(pem: bytes) -> tuple[int, int]:
    der = b"".join(
        line.strip()
        for line in pem.splitlines()
        if not line.startswith(b"-----") and line.strip()
    )
    spki = base64.b64decode(der)
    outer, _ = _read_der_tlv(spki, 0, 0x30)
    _, algorithm_end = _read_der_tlv(outer, 0, 0x30)
    bit_string, _ = _read_der_tlv(outer, algorithm_end, 0x03)
    if not bit_string or bit_string[0] != 0:
        raise ValueError("Unsupported RSA public key bit string")
    rsa_key = bit_string[1:]
    rsa_seq, _ = _read_der_tlv(rsa_key, 0, 0x30)
    modulus_bytes, offset = _read_der_tlv(rsa_seq, 0, 0x02)
    exponent_bytes, _ = _read_der_tlv(rsa_seq, offset, 0x02)
    return int.from_bytes(modulus_bytes, "big"), int.from_bytes(exponent_bytes, "big")


def _read_der_tlv(data: bytes, offset: int, expected_tag: int) -> tuple[bytes, int]:
    if offset >= len(data) or data[offset] != expected_tag:
        raise ValueError("Unexpected DER tag")
    offset += 1
    length_byte = data[offset]
    offset += 1
    if length_byte & 0x80:
        length_size = length_byte & 0x7F
        length = int.from_bytes(data[offset : offset + length_size], "big")
        offset += length_size
    else:
        length = length_byte
    end = offset + length
    return data[offset:end], end

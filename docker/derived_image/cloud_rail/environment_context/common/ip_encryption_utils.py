import logging
import re
import struct

# pylint: disable=invalid-name
import uuid
from enum import Enum

IP_ADDRESS_REGEX = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'


class EncryptionMode(str, Enum):
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"


def _rotl(b, r):
    return ((b << r) & 0xff) | (b >> (8 - r))


def encode_ips_in_file(file_path: str, customer_id: str, encryption_mode: EncryptionMode):
    with open(file_path) as f:
        content = f.read()
    encrypted_content = encode_ips_in_json(content, customer_id, encryption_mode)
    with open(file_path, "w") as f:
        f.write(encrypted_content)


def encode_ips_in_json(json: str, customer_id: str, encryption_mode: EncryptionMode):
    operation = encrypt if encryption_mode == encryption_mode.ENCRYPT else decrypt
    key = uuid.UUID(customer_id).bytes
    ip_pattern = re.compile(IP_ADDRESS_REGEX)
    matches = list(set(ip_pattern.findall(json)))
    sort_function = lambda ip: tuple(int(part) for part in ip.split('.'))
    matches.sort(key=sort_function, reverse=True)
    result = json
    for match in matches:
        result = result.replace(match, operation(key, match))
    return result


def _permute_fwd(state):
    (b0, b1, b2, b3) = state
    b0 += b1
    b2 += b3
    b0 &= 0xff
    b2 &= 0xff
    b1 = _rotl(b1, 2)
    b3 = _rotl(b3, 5)
    b1 ^= b0
    b3 ^= b2
    b0 = _rotl(b0, 4)
    b0 += b3
    b2 += b1
    b0 &= 0xff
    b2 &= 0xff
    b1 = _rotl(b1, 3)
    b3 = _rotl(b3, 7)
    b1 ^= b2
    b3 ^= b0
    b2 = _rotl(b2, 4)
    return b0, b1, b2, b3


def _permute_bwd(state):
    (b0, b1, b2, b3) = state
    b2 = _rotl(b2, 4)
    b1 ^= b2
    b3 ^= b0
    b1 = _rotl(b1, 5)
    b3 = _rotl(b3, 1)
    b0 -= b3
    b2 -= b1
    b0 &= 0xff
    b2 &= 0xff
    b0 = _rotl(b0, 4)
    b1 ^= b0
    b3 ^= b2
    b1 = _rotl(b1, 6)
    b3 = _rotl(b3, 3)
    b0 -= b1
    b2 -= b3
    b0 &= 0xff
    b2 &= 0xff
    return b0, b1, b2, b3


def _xor4(x, y):
    return [(x[i] ^ y[i]) & 0xff for i in (0, 1, 2, 3)]


def encrypt(key, ip):
    """16-byte key, ip string like '192.168.1.2'"""
    k = [struct.unpack('<B', bytes([x]))[0] for x in key]
    try:
        state = [int(x) for x in ip.split('.')]
    except ValueError:
        logging.exception('ValueError in encrypt for key = {}, ip = {}'.format(key, ip))
        raise
    try:
        state = _xor4(state, k[:4])
        state = _permute_fwd(state)
        state = _xor4(state, k[4:8])
        state = _permute_fwd(state)
        state = _xor4(state, k[8:12])
        state = _permute_fwd(state)
        state = _xor4(state, k[12:16])
    except IndexError:
        logging.exception('IndexError in encrypt for key = {}, ip = {}'.format(key, ip))
        raise
    return '.'.join(str(x) for x in state)


def decrypt(key, ip):
    """16-byte key, encrypted ip string like '215.51.199.127'"""
    k = [struct.unpack('<B', bytes([x]))[0] for x in key]
    try:
        state = [int(x) for x in ip.split('.')]
    except ValueError:
        logging.exception('ValueError in encrypt for key = {}, ip = {}'.format(key, ip))
        raise
    try:
        state = _xor4(state, k[12:16])
        state = _permute_bwd(state)
        state = _xor4(state, k[8:12])
        state = _permute_bwd(state)
        state = _xor4(state, k[4:8])
        state = _permute_bwd(state)
        state = _xor4(state, k[:4])
    except IndexError:
        logging.exception('IndexError in encrypt for key = {}, ip = {}'.format(key, ip))
        raise
    return '.'.join(str(x) for x in state)

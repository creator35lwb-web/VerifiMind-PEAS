"""
UUID Helper — v0.5.6 Gateway
UUIDv7-compatible timestamp-ordered UUID generation.

UUIDv7 provides timestamp-ordered identifiers for better database indexing
(recommended by AI Council, MACP-2026-03-17-COUNCIL-ROADMAP).

Python 3.13 adds uuid.uuid7() natively. For earlier versions, we implement
a compatible format: 48-bit ms timestamp + version/variant bits + random.
"""
import os
import time
import uuid


def generate_ea_uuid() -> str:
    """Generate a UUIDv7-compatible timestamp-ordered UUID for EA registration.

    Format: xxxxxxxx-xxxx-7xxx-yxxx-xxxxxxxxxxxx
    - Bits 0-47:  Unix timestamp in milliseconds (48 bits)
    - Bits 48-51: Version = 7 (4 bits)
    - Bits 52-63: Random (12 bits)
    - Bits 64-65: Variant = 10 (2 bits)
    - Bits 66-127: Random (62 bits)

    Returns:
        UUID string in standard 8-4-4-4-12 format
    """
    # 48-bit millisecond timestamp
    ts_ms = int(time.time() * 1000)
    ts_hex = ts_ms & 0xFFFFFFFFFFFF  # 48 bits

    # 12 random bits for time section
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF

    # 62 random bits for node section (variant 10b prepended)
    rand_b = int.from_bytes(os.urandom(8), "big")
    rand_b = (rand_b & 0x3FFFFFFFFFFFFFFF) | 0x8000000000000000  # set variant bits

    # Pack into UUID fields
    time_high = (ts_hex >> 16) & 0xFFFFFFFF
    time_mid = ts_hex & 0xFFFF
    time_low_and_version = 0x7000 | rand_a  # version 7

    uuid_int = (
        (time_high << 96)
        | (time_mid << 80)
        | (time_low_and_version << 64)
        | rand_b
    )

    return str(uuid.UUID(int=uuid_int))


def generate_feedback_id() -> str:
    """Generate a standard UUIDv4 for feedback records."""
    return str(uuid.uuid4())

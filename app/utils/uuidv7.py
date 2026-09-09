import os
import time
import uuid


def uuidv7() -> uuid.UUID:
    """
    Generate a UUIDv7 based on RFC 9562.
    UUIDv7 format:
      - 48 bits: Unix timestamp in milliseconds
      - 4 bits: Version (0111)
      - 12 bits: Random data
      - 2 bits: Variant (10)
      - 62 bits: Random data
    """
    # 48-bit timestamp in milliseconds
    ns = time.time_ns()
    timestamp_ms = ns // 1_000_000

    # 10 random bytes (80 bits)
    rand_bytes = bytearray(os.urandom(10))

    # Pack 48-bit timestamp into 6 bytes
    time_bytes = timestamp_ms.to_bytes(6, byteorder="big")

    # Combine into 16 bytes
    raw = bytearray(16)
    raw[0:6] = time_bytes
    raw[6:8] = rand_bytes[0:2]
    raw[8:16] = rand_bytes[2:10]

    # Set version 7: 0b01110000 = 0x70
    raw[6] = (raw[6] & 0x0F) | 0x70
    # Set variant 10: 0b10000000 = 0x80
    raw[8] = (raw[8] & 0x3F) | 0x80

    return uuid.UUID(bytes=bytes(raw))


SQL_CREATE_UUIDV7_FUNCTION = """
CREATE OR REPLACE FUNCTION uuidv7() RETURNS uuid AS $$
DECLARE
  v_time timestamp with time zone := clock_timestamp();
  v_epoch_ms bigint := (EXTRACT(EPOCH FROM v_time) * 1000)::bigint;
  v_hex text := lpad(to_hex(v_epoch_ms), 12, '0');
  v_rand text := md5(random()::text || clock_timestamp()::text);
BEGIN
  RETURN (
    substr(v_hex, 1, 8) || '-' ||
    substr(v_hex, 9, 4) || '-' ||
    '7' || substr(v_rand, 1, 3) || '-' ||
    to_hex(8 + (random() * 3)::int) || substr(v_rand, 4, 3) || '-' ||
    substr(v_rand, 7, 12)
  )::uuid;
END;
$$ LANGUAGE plpgsql VOLATILE;
"""

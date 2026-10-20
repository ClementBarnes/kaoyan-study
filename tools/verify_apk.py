#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strict APK verifier using RAW zip parsing (no zipfile name normalization).

Why raw: Python's zipfile silently normalizes central-directory entry names
(backslash -> slash) when reading, which hid the on-device asset breakage from
every desktop check. This tool parses the central directory and local file
headers byte-by-byte and requires exact agreement, forward slashes only.

Checks (all must pass):
  1. every entry: RAW central name == RAW local name, forward slashes only
  2. required entries present (manifest / dex / arsc / www/index.html)
  3. exactly 385 mp3 files under assets/www/audio/
  4. no duplicate entry names
  5. zip CRC integrity (testzip)

Usage: verify_apk.py <apk> [apk2 ...]
Exit 0 only if every file passes every check.
"""

import struct
import sys
import zipfile

REQUIRED = [
    "AndroidManifest.xml",
    "classes.dex",
    "resources.arsc",
    "assets/www/index.html",
]
EXPECTED_MP3 = 385


def read_eocd(data: bytes):
    i = data.rfind(b"PK\x05\x06")
    if i < 0:
        raise ValueError("EOCD not found")
    _sig, _disk, _cddisk, _dents, tents, cd_size, cd_off, _clen = struct.unpack_from(
        "<IHHHHIIH", data, i)
    return tents, cd_size, cd_off


def raw_entries(data: bytes):
    """[(raw_central_name, raw_local_name)] in central-directory order."""
    tents, _cd_size, cd_off = read_eocd(data)
    out = []
    p = cd_off
    for _ in range(tents):
        sig, = struct.unpack_from("<I", data, p)
        if sig != 0x02014B50:
            raise ValueError("bad central signature at %d" % p)
        n, m, k = struct.unpack_from("<HHH", data, p + 28)
        loff, = struct.unpack_from("<I", data, p + 42)
        cname = data[p + 46:p + 46 + n]
        lsig, = struct.unpack_from("<I", data, loff)
        if lsig != 0x04034B50:
            raise ValueError("bad local signature at %d" % loff)
        ln, lm = struct.unpack_from("<HH", data, loff + 26)
        lname = data[loff + 30:loff + 30 + ln]
        out.append((cname, lname))
        p += 46 + n + m + k
    return out


def check(path: str) -> bool:
    problems = []
    try:
        data = open(path, "rb").read()
        raw = raw_entries(data)
    except Exception as e:
        print("[FAIL] %s: cannot parse (%s)" % (path, e))
        return False

    names = []
    mismatch = 0
    backslash = 0
    for cname, lname in raw:
        names.append(cname.decode("utf-8", "replace"))
        if cname != lname:
            mismatch += 1
        if b"\\" in cname or b"\\" in lname:
            backslash += 1
    if mismatch:
        problems.append("%d entries: raw local header != raw central directory" % mismatch)
    if backslash:
        problems.append("%d entries contain backslash (raw)" % backslash)

    for must in REQUIRED:
        if must not in names:
            problems.append("missing entry: " + must)

    mp3 = [n for n in names if n.startswith("assets/www/audio/") and n.endswith(".mp3")]
    if len(mp3) != EXPECTED_MP3:
        problems.append("mp3 count %d != %d" % (len(mp3), EXPECTED_MP3))

    dup = len(names) - len(set(names))
    if dup:
        problems.append("%d duplicate entry names" % dup)

    # CRC integrity via zipfile (safe now: raw names are already normalized)
    try:
        bad_crc = zipfile.ZipFile(path).testzip()
        if bad_crc is not None:
            problems.append("CRC failed on: " + bad_crc)
    except Exception as e:
        problems.append("zipfile integrity error: %s" % e)

    if problems:
        print("[FAIL] %s" % path)
        for p in problems:
            print("   - " + p)
        return False
    print("[PASS] %s  (%d entries, %d mp3, raw local/central consistent)" %
          (path, len(names), len(mp3)))
    return True


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: verify_apk.py <apk> [apk2 ...]")
        sys.exit(2)
    ok = all(check(p) for p in sys.argv[1:])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

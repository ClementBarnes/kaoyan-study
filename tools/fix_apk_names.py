#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalize ALL zip entry names in an unsigned APK to forward slashes,
in BOTH the local file headers and the central directory.

Root cause this fixes:
  `aapt2 link -A` on Windows writes asset entry names with backslashes
  (assets/www\\audio\\x.mp3) in BOTH structures. Desktop tools hide this:
  Python's zipfile normalizes central-directory names on read, unzip mixes
  separators in display. Android's AssetManager uses the raw names, so on
  device every asset resolves to a flat name like `www\\audio\\x.mp3` and
  AssetManager.open("www/index.html") throws FileNotFoundException.

Method: rebuild the zip entry-by-entry with clean names (repack is provably
consistent; byte patching is not, because the central directory is also
affected). Self-verifies with a RAW parser (no zipfile normalization) before
exiting; exits non-zero on any residual backslash or local/central mismatch.
"""

import os
import struct
import sys
import zipfile

EOCD_SIG = b"PK\x05\x06"


def read_eocd(data: bytes):
    i = data.rfind(EOCD_SIG)
    if i < 0:
        sys.exit("[ERROR] EOCD not found")
    _sig, _disk, _cddisk, _dents, tents, cd_size, cd_off, _clen = struct.unpack_from(
        "<IHHHHIIH", data, i)
    return tents, cd_size, cd_off


def raw_central_names(data: bytes):
    """Return [(raw_name_bytes, local_header_offset)] straight from the central dir."""
    tents, _cd_size, cd_off = read_eocd(data)
    out = []
    p = cd_off
    for _ in range(tents):
        sig, = struct.unpack_from("<I", data, p)
        if sig != 0x02014B50:
            sys.exit("[ERROR] bad central signature at %d" % p)
        n, m, k = struct.unpack_from("<HHH", data, p + 28)
        loff, = struct.unpack_from("<I", data, p + 42)
        out.append((data[p + 46:p + 46 + n], loff))
        p += 46 + n + m + k
    return out


def raw_local_name(data: bytes, loff: int) -> bytes:
    sig, = struct.unpack_from("<I", data, loff)
    if sig != 0x04034B50:
        sys.exit("[ERROR] bad local signature at %d" % loff)
    n, m = struct.unpack_from("<HH", data, loff + 26)
    return data[loff + 30:loff + 30 + n]


def repack(path: str) -> int:
    data = open(path, "rb").read()
    raw = raw_central_names(data)
    names = []
    for raw_name, _loff in raw:
        clean = raw_name.replace(b"\\", b"/").decode("utf-8")
        names.append(clean)
    dup = len(names) - len(set(names))
    if dup:
        sys.exit("[ERROR] normalization would create %d duplicate names" % dup)

    zin = zipfile.ZipFile(path)
    tmp = path + ".repack"
    with zipfile.ZipFile(tmp, "w") as zout:
        for (raw_name, _loff), clean in zip(raw, names):
            if b"\\" not in raw_name:
                src_name = clean
            else:
                src_name = None
            # zipfile normalizes backslashes on read, so look up by the
            # normalized form; fall back to a per-info match if needed.
            info = None
            for zi in zin.infolist():
                if zi.filename.encode("utf-8") == raw_name or \
                   zi.filename.encode("utf-8") == raw_name.replace(b"\\", b"/"):
                    info = zi
                    break
            if info is None:
                sys.exit("[ERROR] cannot map entry %r" % raw_name)
            payload = zin.read(info)
            nzi = zipfile.ZipInfo(clean, date_time=info.date_time)
            nzi.compress_type = info.compress_type
            nzi.external_attr = info.external_attr
            nzi.internal_attr = info.internal_attr
            nzi.create_system = info.create_system
            zout.writestr(nzi, payload)
    zin.close()
    os.replace(tmp, path)
    return sum(1 for n, _ in raw if b"\\" in n)


def self_check(path: str) -> bool:
    data = open(path, "rb").read()
    raw = raw_central_names(data)
    bad = []
    for raw_name, loff in raw:
        lname = raw_local_name(data, loff)
        if b"\\" in raw_name or b"\\" in lname or raw_name != lname:
            bad.append((raw_name, lname))
    if bad:
        print("[ERROR] %d entries still inconsistent (raw parse):" % len(bad))
        for c, l in bad[:5]:
            print("   central=%r local=%r" % (c, l))
        return False
    return True


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: fix_apk_names.py <apk>")
        sys.exit(2)
    path = sys.argv[1]
    count = repack(path)
    ok = self_check(path)
    print("repacked %d backslash entries; raw-parse check: %s"
          % (count, "OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

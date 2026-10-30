#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trim TerraMaster usb_initboot image: keep MBR + GPT + the only "primary"
partition (~120 MB) and drop the trailing unallocated space, then rebuild
a self-consistent GPT (backup header + backup entries) so the result is a
valid 120 MiB disk image that can be flashed with Etcher/Rufus.

Usage:
    python3 trim.py <input.img> <output.img>

Example:
    python3 trim.py usb_initboot_legacy_2037.img usb_initboot_legacy_2037_120mb.img

Why:
    The official image (e.g. 2037) is a truncated 230 MiB image of a disk
    that GPT claims to be 3.75 GiB. It contains ONE partition named
    "primary" (LBA 34..245726, about 120 MB / ext filesystem); everything
    after it is unallocated. If you flash the 230 MiB image onto the
    built-in 120 MB USB stick of a TerraMaster F4-225 (or similar), the
    extra ~110 MiB tail does not fit and upgrade to TOS 7 may fail.
    This script produces a clean 120 MiB image with a valid backup GPT.

Notes:
    - Requires Python 3 (standard library only, no pip packages).
    - The partition content is copied byte-for-byte; the ext filesystem
      inside is untouched.
"""
import argparse
import os
import struct
import sys
import zlib

SEC = 512
FIRST_USABLE = 34          # LBA of first usable sector (standard GPT)
NUM_ENTRIES = 128
ENTRY_SIZE = 128
ENTRIES_SECTORS = NUM_ENTRIES * ENTRY_SIZE // SEC  # 32


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def build_header(current_lba, backup_lba, entries_lba, disk_guid, entries_crc, last_usable):
    """Build a 512-byte GPT header (CRC over the first 92 bytes)."""
    h = bytearray(92)
    h[0:8] = b"EFI PART"
    h[8:12] = struct.pack("<I", 0x00010000)   # revision 1.0
    h[12:16] = struct.pack("<I", 92)          # header size
    h[20:24] = struct.pack("<I", 0)           # reserved
    h[24:32] = struct.pack("<Q", current_lba)
    h[32:40] = struct.pack("<Q", backup_lba)
    h[40:48] = struct.pack("<Q", FIRST_USABLE)
    h[48:56] = struct.pack("<Q", last_usable)
    h[56:72] = disk_guid
    h[72:80] = struct.pack("<Q", entries_lba)
    h[80:84] = struct.pack("<I", NUM_ENTRIES)
    h[84:88] = struct.pack("<I", ENTRY_SIZE)
    h[88:92] = struct.pack("<I", entries_crc)
    h[16:20] = b"\0\0\0\0"                    # zero CRC field, then compute
    h[16:20] = struct.pack("<I", crc32(bytes(h)))
    return bytes(h).ljust(SEC, b"\x00")


def read_lba(f, lba, n=1):
    f.seek(lba * SEC)
    return f.read(n * SEC)


def write_lba(f, lba, data):
    assert len(data) % SEC == 0
    f.seek(lba * SEC)
    f.write(data)


def main():
    parser = argparse.ArgumentParser(description="Trim TerraMaster usb_initboot image to 120 MiB")
    parser.add_argument("input", help="path to the original .img (e.g. 230 MiB)")
    parser.add_argument("output", help="path for the trimmed .img (120 MiB)")
    args = parser.parse_args()

    with open(args.input, "rb") as src:
        mbr = read_lba(src, 0)
        assert mbr[510:512] == b"\x55\xaa", "MBR signature missing"

        # --- parse protective MBR entry (16 bytes at 0x1BE) ---
        p = 0x1BE
        assert mbr[p + 4] == 0xEE, "MBR entry is not a GPT protective partition"
        assert struct.unpack_from("<I", mbr, p + 8)[0] == 1, "unexpected MBR start LBA"
        mbr = bytearray(mbr)

        # --- parse primary GPT header (LBA 1) ---
        hdr = read_lba(src, 1)
        assert hdr[:8] == b"EFI PART", "GPT signature missing"
        disk_guid = hdr[56:72]

        # --- partition entries (LBA 2..33, 128 x 128 bytes) ---
        entries = read_lba(src, 2, ENTRIES_SECTORS)
        entries_crc = crc32(entries)
        stored_crc = struct.unpack_from("<I", hdr, 88)[0]
        if entries_crc != stored_crc:
            print(f"warning: entries CRC mismatch (stored={stored_crc:08x}, computed={entries_crc:08x})")

        # --- the only partition: LBA 34 .. partition_last_lba ---
        first = struct.unpack_from("<Q", entries, 32)[0]
        partition_last_lba = struct.unpack_from("<Q", entries, 40)[0]
        assert first == 34, f"unexpected partition start LBA: {first}"
        print(f"partition 'primary': LBA {first} .. {partition_last_lba} "
              f"({(partition_last_lba - first + 1) * SEC / 1e6:.1f} MB)")

        part_bytes = read_lba(src, first, partition_last_lba - first + 1)

    # --- assemble the new image ---
    n = partition_last_lba + 1 + ENTRIES_SECTORS + 1   # entries + backup header after partition
    backup_entries_lba = partition_last_lba + 1
    backup_header_lba = n - 1

    with open(args.output, "wb") as out:
        out.truncate(n * SEC)
        struct.pack_into("<I", mbr, p + 12, backup_header_lba)  # protective MBR size
        write_lba(out, 0, bytes(mbr))
        write_lba(out, 1, build_header(1, backup_header_lba, 2, disk_guid, entries_crc, partition_last_lba))
        write_lba(out, 2, entries)
        write_lba(out, first, part_bytes)
        write_lba(out, backup_entries_lba, entries)
        write_lba(out, backup_header_lba,
                  build_header(backup_header_lba, 1, backup_entries_lba, disk_guid, entries_crc, partition_last_lba))

    size = os.path.getsize(args.output)
    print(f"output : {args.output}")
    print(f"size   : {size} bytes = {size / 1024 / 1024:.3f} MiB ({size / 1e6:.2f} MB decimal)")


if __name__ == "__main__":
    main()
#（注：内容由AI生成）

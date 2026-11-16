#!/usr/bin/env python3
"""从内核二进制中解析 linux_banner，输出 KEY=VALUE（供 GitHub Actions source）。"""
from __future__ import annotations

import re
import sys


def parse_banner(banner: str) -> dict[str, str]:
    # Linux version 5.15.211-gdb39b3851f98 (root@host) (CC...), LLD ...) #1 SMP PREEMPT <ts>
    m = re.match(
        r"Linux version (?P<release>[^ ]+) "
        r"\((?P<user>[^@]+)@(?P<host>[^)]+)\) "
        r"\((?P<toolchain>.*)\) "
        r"#(?P<ver>\d+) SMP PREEMPT (?P<ts>.+)$",
        banner.strip(),
    )
    if not m:
        raise SystemExit(f"cannot parse banner:\n{banner}")

    toolchain = m.group("toolchain")
    if "), LLD " in toolchain:
        cc, ld = toolchain.split("), LLD ", 1)
        cc = cc + ")"
        ld = "LLD " + ld
    else:
        cc, ld = toolchain, ""

    release = m.group("release")
    if "-" not in release:
        raise SystemExit(f"unexpected release (no localversion): {release}")
    localver = "-" + release.split("-", 1)[1]
    hash_part = localver[2:] if localver.startswith("-g") else localver.lstrip("-")

    return {
        "EXPECTED_RELEASE": release,
        "LOCALVER": localver,
        "BANNER_HASH": hash_part,
        "KBUILD_BUILD_USER": m.group("user"),
        "KBUILD_BUILD_HOST": m.group("host"),
        "KBUILD_BUILD_TIMESTAMP": m.group("ts"),
        "KBUILD_BUILD_VERSION": m.group("ver"),
        "CC_VERSION": cc,
        "LD_VERSION": ld,
    }


def main(path: str) -> None:
    data = open(path, "rb").read()
    i = data.find(b"Linux version 5.15")
    if i < 0:
        raise SystemExit("linux banner not found")
    banner = data[i : i + 800].split(b"\x00")[0].decode("utf-8", "replace")
    fields = parse_banner(banner)
    print(f"BANNER={banner}")
    for k, v in fields.items():
        # multiline-safe for GITHUB_ENV: use simple values only
        if "\n" in v:
            raise SystemExit(f"{k} contains newline")
        print(f"{k}={v}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <kernel-or-Image>")
    main(sys.argv[1])

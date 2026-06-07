"""Download raw OpenFlights source files.

This script is the first reproducible step in the mini-project pipeline.
It downloads the public OpenFlights data used by later scripts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlretrieve


BASE_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data"
RAW_DIR = Path("raw_data")
FILES = ("airports.dat", "airlines.dat", "routes.dat")


def download_file(filename: str, force: bool) -> None:
    RAW_DIR.mkdir(exist_ok=True)
    output_path = RAW_DIR / filename

    if output_path.exists() and output_path.stat().st_size > 0 and not force:
        print(f"Exists: {output_path}")
        return

    source_url = f"{BASE_URL}/{filename}"
    print(f"Downloading {source_url}")
    urlretrieve(source_url, output_path)
    print(f"Saved: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download OpenFlights raw data files.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even when they already exist.",
    )
    args = parser.parse_args()

    for filename in FILES:
        download_file(filename, force=args.force)


if __name__ == "__main__":
    main()

"""Read a local presigned URL and record an HTTP probe without logging the URL.

Usage: py tools/probe_presigned.py local/presigned-old.txt
Only use with the group's disposable S3 test image. Does not need AWS credentials.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url_file", type=Path)
    args = parser.parse_args()
    try:
        url = args.url_file.read_text(encoding="utf-8-sig").strip()
    except OSError:
        parser.exit(1, "Không đọc được file URL. Kiểm tra đường dẫn.\n")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".amazonaws.com"):
        parser.exit(1, "Chỉ dùng URL HTTPS của S3 AWS trong bài thử này.\n")
    if parsed.username or parsed.password or parsed.fragment or "\n" in url or "\r" in url:
        parser.exit(1, "Định dạng URL không hợp lệ.\n")
    params = urllib.parse.parse_qs(parsed.query)
    record = {
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_file": args.url_file.name,
        "signed_at_utc": params.get("X-Amz-Date", [None])[0],
        "expires_in_seconds": params.get("X-Amz-Expires", [None])[0],
    }
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            record["http_status"] = response.status
            record["content_type"] = response.headers.get("Content-Type")
            record["bytes_read"] = len(response.read(1024 * 1024))
    except urllib.error.HTTPError as error:
        record["http_status"] = error.code
        try:
            root = ET.fromstring(error.read(16384))
            record["s3_error_code"] = root.findtext("Code") or "UNKNOWN"
        except ET.ParseError:
            record["s3_error_code"] = "NON_XML_ERROR"
    except (urllib.error.URLError, TimeoutError):
        record["http_status"] = None
        record["s3_error_code"] = "NETWORK_ERROR"
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

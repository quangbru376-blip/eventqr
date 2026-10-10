"""EventQR week 1: GET /web/{page} serves a permitted HTML file from private S3.

AI-assisted draft; deploy with existing LabRole. WEB_BUCKET is required.
Only index.html is exposed in this week 1 version. No QR/email/secret objects.
"""
import logging
import os

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ALLOWED_PAGES = {"index.html"}
MAX_HTML_BYTES = 1024 * 1024


def response(status_code, body, content_type="text/plain; charset=utf-8"):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": content_type,
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Permissions-Policy": "camera=(self), microphone=()",
        },
        "body": body,
        "isBase64Encoded": False,
    }


def lambda_handler(event, context):
    if event.get("httpMethod") != "GET":
        return response(405, "Method not allowed")

    page = (event.get("pathParameters") or {}).get("page", "")
    if page not in ALLOWED_PAGES:
        return response(404, "Page not found")

    bucket = os.environ.get("WEB_BUCKET")
    if not bucket:
        logger.error("WEB_BUCKET_NOT_CONFIGURED")
        return response(500, "WEB_BUCKET is not configured")

    try:
        obj = s3.get_object(Bucket=bucket, Key=page)
        body_stream = obj["Body"]
        try:
            raw = body_stream.read(MAX_HTML_BYTES + 1)
        finally:
            body_stream.close()
        if len(raw) > MAX_HTML_BYTES:
            logger.error("WEB_FILE_TOO_LARGE")
            return response(500, "Web file exceeds the week 1 size limit")
        html = raw.decode("utf-8-sig")
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "Unknown")
        logger.error("S3_READ_FAILED code=%s", code)
        if code in {"NoSuchKey", "404", "NotFound"}:
            return response(404, "Web file not found")
        return response(500, "Cannot read web file; check Lambda logs")
    except UnicodeDecodeError:
        logger.error("WEB_FILE_NOT_UTF8")
        return response(500, "Save the HTML file as UTF-8")

    logger.info("WEB_PAGE_SERVED")
    return response(200, html, "text/html; charset=utf-8")

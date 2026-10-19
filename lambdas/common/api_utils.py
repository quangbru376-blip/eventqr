"""AI-assisted Week 2 helpers. Configure through Lambda environment variables."""
import json
import logging
import os
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class InputError(ValueError):
    pass


def uuid_text(value):
    if not isinstance(value, str):
        raise InputError('ID phải là chuỗi UUID')
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        raise InputError('ID phải là UUID hợp lệ') from None
    if str(parsed) != value:
        raise InputError('UUID phải viết thường, đúng định dạng có dấu gạch ngang')
    return value


def body_json(event):
    if event.get('isBase64Encoded'):
        raise InputError('Body phải là JSON UTF-8 thông thường')
    try:
        body = json.loads(event.get('body') or '{}')
    except (ValueError, TypeError):
        raise InputError('Body không phải JSON hợp lệ') from None
    if not isinstance(body, dict):
        raise InputError('Body phải là JSON object')
    return body


def reply(status, data=None, code=None, message=None):
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
    }
    origin = os.environ.get('CORS_ORIGIN', '').strip()
    if origin:
        headers.update({
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Vary': 'Origin',
        })
    payload = {'ok': True, 'data': data or {}} if code is None else {
        'ok': False, 'error': {'code': code, 'message': message, 'details': {}}
    }
    return {'statusCode': status, 'headers': headers,
            'body': json.dumps(payload, ensure_ascii=False), 'isBase64Encoded': False}


def error(status, code, message):
    return reply(status, code=code, message=message)


def log_failure(label, exc):
    # Log only a safe AWS error code/type, never a body, email, URL or payload.
    aws_code = getattr(exc, 'response', {}).get('Error', {}).get('Code')
    logger.error('%s code=%s', label, aws_code or type(exc).__name__)

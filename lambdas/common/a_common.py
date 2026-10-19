"""AI-assisted EventQR A helpers; no credentials or ticket payloads in logs."""
import base64
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit

import boto3
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)
_secret = None


class InputError(ValueError):
    pass


def env(name):
    value = os.environ.get(name, '').strip()
    if not value:
        logger.error('CONFIG_MISSING name=%s', name)
        raise RuntimeError('Missing configuration')
    return value


def uuid_text(value):
    if not isinstance(value, str):
        raise InputError('ID phải là chuỗi UUID')
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        raise InputError('ID phải là UUID hợp lệ') from None
    if str(parsed) != value:
        raise InputError('UUID phải viết thường theo định dạng có gạch ngang')
    return value


def text(value, label, limit):
    if not isinstance(value, str):
        raise InputError(f'{label} phải là chuỗi')
    value = value.strip()
    if not 1 <= len(value) <= limit or any(ord(c) < 32 for c in value):
        raise InputError(f'{label} phải có từ 1 đến {limit} ký tự, không có ký tự điều khiển')
    return value


def email_text(value):
    value = text(value, 'Email', 254).lower()
    if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', value):
        raise InputError('Email không đúng định dạng')
    return value


def start_time(value):
    if not isinstance(value, str) or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value):
        raise InputError('startTime cần ISO 8601 có múi giờ, ví dụ 2026-10-25T08:00:00+07:00')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    except ValueError:
        raise InputError('startTime không phải ngày giờ hợp lệ') from None


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def body_json(event):
    raw = event.get('body')
    if not isinstance(raw, str) or len(raw) > 32768:
        raise InputError('Body cần là chuỗi JSON hợp lệ, tối đa 32 KB')
    try:
        if event.get('isBase64Encoded'):
            raw = base64.b64decode(raw, validate=True).decode('utf-8')
        body = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise InputError('Body không phải JSON UTF-8 hợp lệ') from None
    if not isinstance(body, dict):
        raise InputError('Body phải là JSON object')
    return body


def reply(status, data=None, code=None, message=None, details=None):
    headers = {'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
               'X-Content-Type-Options': 'nosniff'}
    origin = os.environ.get('CORS_ORIGIN', '').strip()
    if origin:
        headers.update({'Access-Control-Allow-Origin': origin,
                        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type,x-api-key', 'Vary': 'Origin'})
    result = {'ok': True, 'data': data or {}} if code is None else {
        'ok': False, 'error': {'code': code, 'message': message, 'details': details or {}}}
    return {'statusCode': status, 'headers': headers,
            'body': json.dumps(result, ensure_ascii=False), 'isBase64Encoded': False}


def error(status, code, message, details=None):
    return reply(status, code=code, message=message, details=details)


def failure(label, exc):
    safe_code = getattr(exc, 'response', {}).get('Error', {}).get('Code')
    logger.error('%s code=%s', label, safe_code or type(exc).__name__)


def secret_data():
    global _secret
    if _secret is None:
        sm = boto3.client('secretsmanager', config=Config(
            connect_timeout=2, read_timeout=4, retries={'total_max_attempts': 1}))
        raw = sm.get_secret_value(SecretId=env('SECRET_NAME'))
        obj = json.loads(raw['SecretString'])
        key = obj.get('key')
        if not isinstance(key, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', key):
            raise ValueError('Invalid HMAC key format')
        kid = obj.get('kid')
        if not isinstance(kid, str) or not kid:
            raise ValueError('Missing kid')
        _secret = (bytes.fromhex(key), kid)
    return _secret


def ticket_url(event_id, ticket_id):
    base = env('WEB_BASE_URL').rstrip('/')
    parsed = urlsplit(base)
    if (parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment
            or any(c in base for c in '<>') or parsed.username or parsed.password):
        raise ValueError('Invalid WEB_BASE_URL')
    return base + '/ticket.html?' + urlencode({'e': event_id, 't': ticket_id})

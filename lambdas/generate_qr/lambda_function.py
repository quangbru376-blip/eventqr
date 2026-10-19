"""AI-assisted: internal synchronous Lambda; LabRole, no public API route."""
import io
import json
import logging
import os

import boto3
import segno

from api_utils import uuid_text, log_failure
from hmac_utils import sign_ticket

s3 = boto3.client('s3')
secrets = boto3.client('secretsmanager')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
_key = None


def signing_key():
    global _key
    if _key is None:
        raw = secrets.get_secret_value(SecretId=os.environ['SECRET_NAME'])
        secret = json.loads(raw['SecretString'])
        text = secret.get('key')
        if not isinstance(text, str) or len(text) != 64:
            raise ValueError('Secret key must contain 64 hexadecimal characters')
        key = bytes.fromhex(text)
        if len(key) != 32 or not isinstance(secret.get('kid'), str) or not secret['kid']:
            raise ValueError('Invalid key/kid')
        _key = key
    return _key


def lambda_handler(event, context):
    try:
        if not isinstance(event, dict):
            raise ValueError('Input must be an object')
        event_id = uuid_text(event.get('eventId'))
        ticket_id = uuid_text(event.get('ticketId'))
        payload = sign_ticket(event_id, ticket_id, signing_key())
        image = io.BytesIO()
        segno.make_qr(payload, error='m').save(image, kind='png', scale=6, border=4)
        qr_key = f'qr/{event_id}/{ticket_id}.png'
        s3.put_object(
            Bucket=os.environ['QR_BUCKET'], Key=qr_key, Body=image.getvalue(),
            ContentType='image/png', CacheControl='no-store',
            ServerSideEncryption='AES256',
        )
        logger.info('QR_CREATED')
        return {'qrKey': qr_key}
    except Exception as exc:
        log_failure('QR_CREATE_FAILED', exc)
        # Internal error only: do not leak secret/client exception details.
        raise RuntimeError('QR_GENERATION_FAILED') from None

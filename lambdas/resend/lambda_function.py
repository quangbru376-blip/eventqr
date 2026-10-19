"""AI-assisted POST /resend. Recipient comes from DynamoDB, never the request."""
import os

import boto3

from api_utils import InputError, uuid_text, body_json, reply, error, log_failure
from ticket_mail import send_ticket

ddb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return reply(200)
    if event.get('httpMethod') != 'POST':
        return error(405, 'METHOD_NOT_ALLOWED', 'Chỉ hỗ trợ POST')
    try:
        body = body_json(event)
        event_id = uuid_text(body.get('eventId'))
        ticket_id = uuid_text(body.get('ticketId'))
        found = ddb.Table(os.environ['EVENTS_TABLE']).get_item(
            Key={'eventId': event_id}, ConsistentRead=True).get('Item')
        if not found:
            return error(404, 'EVENT_NOT_FOUND', 'Không tìm thấy sự kiện')
        ticket = ddb.Table(os.environ['TICKETS_TABLE']).get_item(
            Key={'eventId': event_id, 'ticketId': ticket_id}, ConsistentRead=True).get('Item')
        if not ticket:
            return error(404, 'TICKET_NOT_FOUND', 'Không tìm thấy vé')
        result = send_ticket(ticket['email'], event_id, ticket_id, found.get('name', 'EventQR'))
        if result == 'PENDING_CONFIRMATION':
            return error(409, 'EMAIL_CONFIRMATION_REQUIRED', 'Xác nhận email SNS rồi bấm gửi lại')
        if result != 'PUBLISHED':
            return error(503, 'EMAIL_DELIVERY_FAILED', 'SNS chưa chấp nhận gửi; thử lại sau')
        return reply(200, {'emailDeliveryStatus': 'PUBLISHED'})
    except InputError as exc:
        return error(400, 'INVALID_INPUT', str(exc))
    except Exception as exc:
        log_failure('RESEND_FAILED', exc)
        return error(500, 'INTERNAL_ERROR', 'Không gửi lại được vé; kiểm tra log Lambda')

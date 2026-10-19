"""AI-assisted shared mail implementation proposed for register AND resend.

Confirm AWS behavior in Learner Lab. Never publish with an unverified filter.
PUBLISHED means SNS accepted a message, not that email reached the inbox.
"""
import json
import os
from urllib.parse import urlencode, urlsplit

import boto3
from botocore.config import Config

from api_utils import uuid_text, log_failure

sns = boto3.client('sns', config=Config(
    connect_timeout=2, read_timeout=3, retries={'total_max_attempts': 1}))


def ensure_subscription(email):
    email = email.strip().lower()
    if not email or '\n' in email or '\r' in email or '@' not in email:
        raise ValueError('Invalid stored email')
    topic = os.environ['SNS_TOPIC_ARN']
    matches = []
    paginator = sns.get_paginator('list_subscriptions_by_topic')
    for page in paginator.paginate(TopicArn=topic):
        for sub in page.get('Subscriptions', []):
            if sub.get('Protocol') == 'email' and sub.get('Endpoint', '').lower() == email:
                matches.append(sub['SubscriptionArn'])
    if len(matches) > 1:
        raise ValueError('Duplicate email subscriptions; inspect SNS console')
    if matches:
        arn = matches[0]
        if not arn.startswith('arn:'):
            return 'PENDING_CONFIRMATION'
    else:
        created = sns.subscribe(
            TopicArn=topic, Protocol='email', Endpoint=email, ReturnSubscriptionArn=True,
            Attributes={'FilterPolicy': json.dumps({'email': [email]}),
                        'FilterPolicyScope': 'MessageAttributes'})
        arn = created['SubscriptionArn']
        if not arn.startswith('arn:'):
            return 'PENDING_CONFIRMATION'
    attrs = sns.get_subscription_attributes(SubscriptionArn=arn)['Attributes']
    if str(attrs.get('PendingConfirmation', '')).lower() == 'true':
        return 'PENDING_CONFIRMATION'
    if str(attrs.get('PendingConfirmation', '')).lower() != 'false':
        raise ValueError('Cannot verify subscription confirmation')
    if attrs.get('FilterPolicyScope', 'MessageAttributes') != 'MessageAttributes':
        raise ValueError('Unexpected filter scope')
    if json.loads(attrs.get('FilterPolicy', '{}')) != {'email': [email]}:
        # Fail closed. Do not change a confirmed filter then immediately publish.
        raise ValueError('Set exact email filter in SNS and wait for propagation')
    return 'CONFIRMED'


def send_ticket(email, event_id, ticket_id, event_name='EventQR'):
    try:
        event_id, ticket_id = uuid_text(event_id), uuid_text(ticket_id)
        email = email.strip().lower()
        if ensure_subscription(email) == 'PENDING_CONFIRMATION':
            return 'PENDING_CONFIRMATION'
        base = os.environ['WEB_BASE_URL'].rstrip('/')
        parsed = urlsplit(base)
        if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError('WEB_BASE_URL must be an HTTPS base URL')
        url = base + '/ticket.html?' + urlencode({'e': event_id, 't': ticket_id})
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'], Subject='EventQR - Ve tham du su kien',
            Message=f'Sự kiện: {event_name}\nMở vé QR tại:\n{url}\nKhông chia sẻ link vé.',
            MessageAttributes={'email': {'DataType': 'String', 'StringValue': email}})
        return 'PUBLISHED'
    except Exception as exc:
        log_failure('TICKET_EMAIL_FAILED', exc)
        return 'FAILED'

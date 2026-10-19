"""AI-assisted local tests with fake AWS services, real B QR/HMAC code.

No network, real credentials, real emails or real HMAC secrets are used.
Run from kit/repo root: py -m unittest discover -s tests -v
The integration test uses this repo's generate_qr source and Segno from its ZIP.
Build dist/eventqr-generate-qr.zip before running the suite (see README.md).
"""
import concurrent.futures
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import sys
import threading
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'lambdas/common'))
QR_PACKAGE = ROOT/'dist/eventqr-generate-qr.zip'
sys.path.insert(0, str(QR_PACKAGE))
E = '11111111-1111-4111-8111-111111111111'
T = '22222222-2222-4222-8222-222222222222'
OTHER = '33333333-3333-4333-8333-333333333333'
os.environ.update(EVENTS_TABLE='events', TICKETS_TABLE='tickets', SECRET_NAME='test-secret',
    QR_BUCKET='test-bucket', SNS_TOPIC_ARN='test-topic', GENERATE_QR_FUNCTION='generate-qr',
    WEB_BASE_URL='https://example.invalid/v1/web', CORS_ORIGIN='https://example.invalid')


class ClientError(Exception):
    def __init__(self, code):
        self.response = {'Error': {'Code': code}}


class Fake:
    def reset(self):
        self.events = {E: {'eventId': E, 'name': 'Su kien thu'}}
        self.tickets = {}
        self.key = secrets.token_hex(32)
        self.lock = threading.Lock()
        self.trace = []
        self.qr_fail = self.db_fail = self.mail_fail = self.bad_filter = False
        self.subscribed = self.confirmed = True
        self.objects = {}
        self.query_calls = 0
        self.secret_calls = 0
        self.sent = []
        self.gen = None

    def Table(self, name):
        fake = self
        class Table:
            def get_item(self, Key, **kwargs):
                data = fake.events.get(Key['eventId']) if name == 'events' else fake.tickets.get((Key['eventId'], Key['ticketId']))
                return {'Item': copy.deepcopy(data)} if data else {}

            def put_item(self, Item, ConditionExpression):
                if name == 'events':
                    if Item['eventId'] in fake.events:
                        raise ClientError('ConditionalCheckFailedException')
                    fake.events[Item['eventId']] = copy.deepcopy(Item)
                    return {}
                fake.trace.append('put')
                if fake.db_fail:
                    raise ClientError('AccessDeniedException')
                key = (Item['eventId'], Item['ticketId'])
                if key in fake.tickets:
                    raise ClientError('ConditionalCheckFailedException')
                assert 'attribute_not_exists(ticketId)' in ConditionExpression
                fake.tickets[key] = copy.deepcopy(Item)
                return {}

            def update_item(self, Key, ConditionExpression, ExpressionAttributeValues, **kwargs):
                assert 'attribute_exists(eventId)' in ConditionExpression
                assert 'attribute_exists(ticketId)' in ConditionExpression
                assert '#s = :issued' in ConditionExpression
                with fake.lock:
                    key = (Key['eventId'], Key['ticketId'])
                    if key not in fake.tickets or fake.tickets[key]['status'] != 'ISSUED':
                        raise ClientError('ConditionalCheckFailedException')
                    fake.tickets[key].update(status='CHECKED_IN', checkedInAt=ExpressionAttributeValues[':at'])
                    return {'Attributes': copy.deepcopy(fake.tickets[key])}

            def query(self, **kwargs):
                fake.query_calls += 1
                assert kwargs['ConsistentRead']
                assert kwargs['ExpressionAttributeValues'][':e'] == E
                items = [copy.deepcopy(v) for (eid, tid), v in fake.tickets.items() if eid == E]
                start = 1 if kwargs.get('ExclusiveStartKey') else 0
                page = {'Items': items[start:] if start else items[:1]}
                if not start and len(items) > 1:
                    page['LastEvaluatedKey'] = {'eventId': E, 'ticketId': items[0]['ticketId']}
                return page
        return Table()

    def get_secret_value(self, **kwargs):
        self.secret_calls += 1
        return {'SecretString': json.dumps({'key': self.key, 'kid': '1'})}

    def invoke(self, **kwargs):
        self.trace.append('qr')
        assert kwargs['InvocationType'] == 'RequestResponse'
        if self.qr_fail:
            return {'StatusCode': 200, 'FunctionError': 'Unhandled', 'Payload': io.BytesIO(b'{"errorMessage":"failed"}')}
        body = json.loads(kwargs['Payload'])
        result = self.gen.lambda_handler(body, None) if self.gen else {'qrKey': f"qr/{body['eventId']}/{body['ticketId']}.png"}
        return {'StatusCode': 200, 'Payload': io.BytesIO(json.dumps(result).encode())}

    def put_object(self, **kwargs):
        self.objects[(kwargs['Bucket'], kwargs['Key'])] = kwargs['Body']

    def get_paginator(self, name):
        return self

    def paginate(self, **kwargs):
        self.trace.append('sns')
        if self.mail_fail:
            raise ClientError('AuthorizationError')
        yield {'Subscriptions': [{'Protocol': 'email', 'Endpoint': 'test@example.invalid',
                                'SubscriptionArn': 'arn:test'}] if self.subscribed else []}

    def subscribe(self, **kwargs):
        assert json.loads(kwargs['Attributes']['FilterPolicy']) == {'email': ['test@example.invalid']}
        self.subscribed = True
        self.confirmed = False
        return {'SubscriptionArn': 'arn:test'}

    def get_subscription_attributes(self, **kwargs):
        return {'Attributes': {'PendingConfirmation': str(not self.confirmed).lower(),
            'FilterPolicyScope': 'MessageAttributes',
            'FilterPolicy': json.dumps({} if self.bad_filter else {'email': ['test@example.invalid']})}}

    def publish(self, **kwargs):
        self.sent.append(kwargs)
        return {'MessageId': 'mock'}


fake = Fake(); fake.reset()
boto = types.ModuleType('boto3')
boto.client = lambda *a, **kw: fake
boto.resource = lambda *a, **kw: fake
sys.modules['boto3'] = boto
sys.modules['botocore'] = types.ModuleType('botocore')
bc = types.ModuleType('botocore.config'); bc.Config = lambda **kw: kw
be = types.ModuleType('botocore.exceptions'); be.ClientError = ClientError
sys.modules['botocore.config'] = bc; sys.modules['botocore.exceptions'] = be


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


create = load('a_create', ROOT/'lambdas/create_event/lambda_function.py')
register = load('a_register', ROOT/'lambdas/register/lambda_function.py')
checkin = load('a_checkin', ROOT/'lambdas/checkin/lambda_function.py')
stats = load('a_stats', ROOT/'lambdas/stats/lambda_function.py')
import a_common
from hmac_utils import sign_ticket


def request(body, method='POST'):
    return {'httpMethod': method, 'body': json.dumps(body)}


def data(result):
    return json.loads(result['body'])['data']


def code(result):
    return json.loads(result['body'])['error']['code']


class ATests(unittest.TestCase):
    def setUp(self):
        fake.reset(); a_common._secret = None

    def register_request(self):
        return request({'eventId': E, 'name': ' Khach thu ', 'email': 'TEST@EXAMPLE.INVALID'})

    def insert_ticket(self, ticket_id=T, status='ISSUED'):
        fake.tickets[(E, ticket_id)] = {'eventId': E, 'ticketId': ticket_id, 'status': status, 'name': 'Khach thu'}
        return sign_ticket(E, ticket_id, bytes.fromhex(fake.key))

    def test_create_event(self):
        result = create.lambda_handler(request({'name': 'Test', 'venue': 'Hoi truong', 'startTime': '2026-10-25T08:00:00+07:00'}), None)
        self.assertEqual(result['statusCode'], 201)
        self.assertEqual(data(result)['startTime'], '2026-10-25T01:00:00Z')
        self.assertIn(data(result)['eventId'], fake.events)

    def test_create_naive_datetime_rejected(self):
        result = create.lambda_handler(request({'name': 'Test', 'venue': 'Hoi truong', 'startTime': '2026-10-25T08:00:00'}), None)
        self.assertEqual(result['statusCode'], 400)

    def test_invalid_json(self):
        self.assertEqual(create.lambda_handler({'httpMethod': 'POST', 'body': '[]'}, None)['statusCode'], 400)

    def test_register_success_order(self):
        result = register.lambda_handler(self.register_request(), None)
        self.assertEqual(result['statusCode'], 201)
        self.assertEqual(fake.trace, ['qr', 'put', 'sns'])
        item = next(iter(fake.tickets.values()))
        self.assertEqual(item['email'], 'test@example.invalid')
        self.assertIn('/v1/web/ticket.html?', data(result)['ticketUrl'])
        self.assertEqual(data(result)['emailDeliveryStatus'], 'PUBLISHED')

    def test_register_qr_failure_no_ticket_or_mail(self):
        fake.qr_fail = True
        result = register.lambda_handler(self.register_request(), None)
        self.assertEqual(result['statusCode'], 500)
        self.assertFalse(fake.tickets); self.assertFalse(fake.sent)

    def test_register_db_failure_no_mail(self):
        fake.db_fail = True
        result = register.lambda_handler(self.register_request(), None)
        self.assertEqual(result['statusCode'], 500); self.assertFalse(fake.sent)

    def test_register_mail_failure_keeps_ticket(self):
        fake.mail_fail = True
        result = register.lambda_handler(self.register_request(), None)
        self.assertEqual(result['statusCode'], 201)
        self.assertEqual(data(result)['emailDeliveryStatus'], 'FAILED'); self.assertEqual(len(fake.tickets), 1)

    def test_register_new_email_autosubscribes(self):
        fake.subscribed = False
        result = register.lambda_handler(self.register_request(), None)
        self.assertEqual(data(result)['emailDeliveryStatus'], 'PENDING_CONFIRMATION')
        self.assertTrue(fake.subscribed); self.assertFalse(fake.sent)

    def test_register_bad_email_rejected(self):
        result = register.lambda_handler(request({'eventId': E, 'name': 'Test', 'email': 'not-an-email'}), None)
        self.assertEqual(result['statusCode'], 400); self.assertFalse(fake.trace)

    def test_register_bad_web_base_before_writes(self):
        with patch.dict(os.environ, {'WEB_BASE_URL': 'https://<api-id>/web'}):
            result = register.lambda_handler(self.register_request(), None)
        self.assertEqual(result['statusCode'], 500); self.assertFalse(fake.tickets); self.assertFalse(fake.trace)

    def test_register_missing_event(self):
        fake.events.clear()
        self.assertEqual(register.lambda_handler(self.register_request(), None)['statusCode'], 404)

    def test_first_and_duplicate_preserves_time(self):
        payload = self.insert_ticket()
        req = request({'eventId': E, 'qrPayload': payload})
        first = checkin.lambda_handler(req, None); second = checkin.lambda_handler(req, None)
        self.assertEqual(first['statusCode'], 200); self.assertEqual(second['statusCode'], 409)
        self.assertEqual(json.loads(second['body'])['error']['details']['checkedInAt'], data(first)['checkedInAt'])

    def test_concurrent_duplicate(self):
        payload = self.insert_ticket(); req = request({'eventId': E, 'qrPayload': payload})
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: checkin.lambda_handler(req, None), [0, 1]))
        self.assertEqual(sorted(r['statusCode'] for r in results), [200, 409])

    def test_modified_signature_no_update(self):
        payload = self.insert_ticket(); payload = payload[:-1] + ('A' if payload[-1] != 'A' else 'B')
        result = checkin.lambda_handler(request({'eventId': E, 'qrPayload': payload}), None)
        self.assertEqual(code(result), 'INVALID_SIGNATURE'); self.assertEqual(fake.tickets[(E,T)]['status'], 'ISSUED')

    def test_wrong_event_no_update(self):
        payload = self.insert_ticket()
        result = checkin.lambda_handler(request({'eventId': OTHER, 'qrPayload': payload}), None)
        self.assertEqual(code(result), 'EVENT_MISMATCH'); self.assertEqual(fake.tickets[(E,T)]['status'], 'ISSUED')

    def test_checkin_missing_event(self):
        payload = self.insert_ticket(); fake.events.clear()
        result = checkin.lambda_handler(request({'eventId': E, 'qrPayload': payload}), None)
        self.assertEqual(code(result), 'EVENT_NOT_FOUND')

    def test_checkin_missing_ticket_no_creation(self):
        payload = sign_ticket(E, T, bytes.fromhex(fake.key))
        result = checkin.lambda_handler(request({'eventId': E, 'qrPayload': payload}), None)
        self.assertEqual(code(result), 'TICKET_NOT_FOUND'); self.assertFalse(fake.tickets)

    def test_wrong_payload_field(self):
        result = checkin.lambda_handler(request({'eventId': E, 'payload': 'test'}), None)
        self.assertEqual(result['statusCode'], 400)

    def test_stats_empty(self):
        result = stats.lambda_handler({'httpMethod': 'GET', 'pathParameters': {'eventId': E}}, None)
        self.assertEqual(data(result)['totalTickets'], 0)

    def test_stats_pagination_and_marker(self):
        self.insert_ticket(); self.insert_ticket(OTHER, 'CHECKED_IN')
        fake.tickets[(E,'EMAIL#marker')] = {'ticketId':'EMAIL#marker'}
        result = stats.lambda_handler({'httpMethod': 'GET', 'pathParameters': {'eventId': E}}, None)
        self.assertEqual(data(result), {'eventId': E, 'totalTickets': 2, 'checkedInTickets': 1, 'notCheckedInTickets': 1})
        self.assertEqual(fake.query_calls, 2)

    def test_stats_unknown_status_not_silently_ignored(self):
        self.insert_ticket(status='BROKEN')
        self.assertEqual(stats.lambda_handler({'httpMethod': 'GET', 'pathParameters': {'eventId': E}}, None)['statusCode'], 500)

    def test_options_and_cors(self):
        for module in [create, register, checkin, stats]:
            result = module.lambda_handler({'httpMethod': 'OPTIONS'}, None)
            self.assertEqual(result['statusCode'], 200)
            self.assertEqual(result['headers']['Access-Control-Allow-Origin'], 'https://example.invalid')

    @unittest.skipUnless(QR_PACKAGE.exists(), 'Build the generate-qr ZIP with Segno first')
    def test_integration_register_real_b_qr_checkin_stats(self):
        gen = load('b_generate_integration', ROOT/'lambdas/generate_qr/lambda_function.py')
        gen._key = None; fake.gen = gen
        created = register.lambda_handler(self.register_request(), None)
        ticket_id = data(created)['ticketId']
        item = fake.tickets[(E, ticket_id)]
        self.assertTrue(fake.objects[('test-bucket', item['qrKey'])].startswith(b'\x89PNG'))
        payload = sign_ticket(E, ticket_id, bytes.fromhex(fake.key))
        req = request({'eventId': E, 'qrPayload': payload})
        self.assertEqual(checkin.lambda_handler(req, None)['statusCode'], 200)
        self.assertEqual(checkin.lambda_handler(req, None)['statusCode'], 409)
        report = stats.lambda_handler({'httpMethod': 'GET', 'pathParameters': {'eventId': E}}, None)
        self.assertEqual(data(report)['checkedInTickets'], 1)


if __name__ == '__main__':
    unittest.main()

from bond import bond
from response_mocker import HTTPError, ResponseMocker
import unittest


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.mocker = ResponseMocker()

    def tearDown(self):
        self.mocker.clear_responses()

    def test_general_raise_for_status(self):
        url = 'https://giant.balloon.com/rides?time=now'
        self.mocker.register_response(url=url, status_code=500, request_verbs=['get'])
        response = self.mocker.get(url)
        with self.assertRaises(HTTPError):
            response.raise_for_status()

    def test_raise_404_for_status(self):
        url = 'https://giant.balloon.com/rides?time=now'
        self.mocker.register_response(url=url, status_code=404, request_verbs=['get'])
        response = self.mocker.get(url)
        with self.assertRaises(HTTPError):
            response.raise_for_status()

    def test_get(self):
        bond.start_test(self)
        self.mocker.register_response(url='https://giant.balloon.com/rides?time=now', status_code=200,
                                      request_verbs=['get'], decoded_json='Sorry, tickets are sold out.')
        response = self.mocker.get('https://giant.balloon.com/rides', params={'time': 'now'})
        bond.spy(get_json=response.json())
        bond.spy(get_url=response.url)
        bond.spy(get_status=response.status_code)

    def test_post(self):
        bond.start_test(self)
        self.mocker.register_response(url='https://oranges.org/squeeze_orange', status_code=201, request_verbs=['post'],
                                      decoded_json='Success.')
        response = self.mocker.post('https://oranges.org/squeeze_orange', headers={'orange_type': 'California'},
                                    payload={'squeeze_level': 5})
        bond.spy(get_json=response.json())
        bond.spy(get_url=response.url)
        bond.spy(get_status=response.status_code)

    def test_request_args(self):
        self.mocker.register_response(url='https://oranges.org/squeeze_orange', status_code=201, request_verbs=['post'],
                                      decoded_json='Success.')
        headers = {'orange_type': 'California'}
        payload = {'squeeze_level': 5}
        response = self.mocker.post('https://oranges.org/squeeze_orange', headers=headers, payload=payload)
        self.assertDictEqual(headers, response.request.args['headers'])
        self.assertDictEqual(payload, response.request.args['payload'])

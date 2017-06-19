from copy import deepcopy
from bond import bond
from response_mocker import HTTPError, ResponseMocker
import unittest


class MiscTests(unittest.TestCase):
    def setUp(self):
        self.mocker = ResponseMocker()

    def tearDown(self):
        self.mocker.clear_responses()

    def test_url_array_parameterization(self):
        bond.start_test(self)
        data = {'a': '1', 'b': '2', 'c': ['4', '5', '6', '7', '8']}
        x = self.mocker._format_params(data)
        bond.spy(array_params=x)

    def test_cannot_alter_responses_via_reference(self):
        bond.start_test(self)
        expected = {'things': 'stuff', 'words': 'series of letters', 'login_date': 'today', 'login_token': 'abcd'}
        self.mocker.register_response(url='https://oranges.org/squeeze_orange', status_code=201, request_verbs=['post'],
                                      decoded_json=expected)
        response = self.mocker.post('https://oranges.org/squeeze_orange', headers={'orange_type': 'California'},
                                    payload={'squeeze_level': 5})
        original = response.json()
        first = deepcopy(original)
        del first['things']
        del first['login_token']
        del first['login_date']
        second = response.json()
        self.assertNotEqual(first, second)
        self.assertEqual(original, second)
        bond.spy(result=second)

    def test_http_error_attributes(self):
        url = 'https://giant.balloon.com/rides?time=now'
        self.mocker.register_response(url=url, status_code=500, request_verbs=['get'])
        response = self.mocker.get(url)
        try:
            response.raise_for_status()
        except HTTPError as httpe:
            exception_dict = httpe.__dict__
            self.assertIn('message', exception_dict)
            self.assertIn('request', exception_dict)
            self.assertIn('response', exception_dict)

    def test_q_depth(self):
        local_mocker = ResponseMocker(request_q_depth=5)
        local_mocker.register_response(url='https://giant.balloon.com/rides?time=now', status_code=200,
                                      request_verbs=['get'], decoded_json='Sorry, tickets are sold out.')
        local_mocker.register_response(url='2', status_code='666', request_verbs=['post'])
        url1 = 'https://giant.balloon.com/rides?time=now'
        url2 = '2'
        for _ in range(5):
            local_mocker.get('https://giant.balloon.com/rides', params={'time': 'now'})
        q = self._get_q_list(local_mocker, 'url')
        url_list = [url1] * 5
        self.assertListEqual(q, url_list)
        local_mocker.post(url='2', decoded_json={'ninjas': 'best'})
        url_list = [url1] * 4
        url_list.append(url2)
        q = self._get_q_list(local_mocker, 'url')
        self.assertListEqual(q, url_list)
        for _ in range(4):
            local_mocker.post(url='2', decoded_json={'ninjas': 'best'})
        url_list = [url2] * 5
        q = self._get_q_list(local_mocker, 'url')
        self.assertListEqual(q, url_list)

    @staticmethod
    def _get_q_list(mocker, attribute=None):
        core = mocker.returned_response_q.queue
        if attribute is None:
            return list(core)
        else:
            return [element.__getattribute__(attribute) for element in core]


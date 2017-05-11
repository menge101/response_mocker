from copy import deepcopy
from bond import bond
from response_mocker import AmbiguousURLMatch, HTTPError, ResponseMocker, UnregisteredURL
import unittest


class ResponseMockerTestCase(unittest.TestCase):
    def setUp(self):
        self.mocker = ResponseMocker()

    def tearDown(self):
        self.mocker.clear_responses()

    def test_register_url(self):
        bond.start_test(self)
        self.mocker.register_response(url='1', status_code='999', request_verbs=['bang'])
        bond.spy(register=self.mocker.responses)

    def test_register_multi(self):
        bond.start_test(self)
        self.mocker.register_response(url='1', status_code='999', request_verbs=['bang'])
        self.mocker.register_response(url='2', status_code='666', request_verbs=['flip'])
        bond.spy(multiURL=self.mocker.responses)

    def test_register_multi_verb(self):
        bond.start_test(self)
        self.mocker.register_response(url='1', status_code='999', request_verbs=['bang', 'boom'])
        bond.spy(multi=self.mocker.responses)

    def test_register_same_url_different_verb(self):
        bond.start_test(self)
        self.mocker.register_response(url='hi.bob', status_code='999', request_verbs=['bang'])
        self.mocker.register_response(url='hi.bob', status_code='999', request_verbs=['boom'])
        bond.spy(sameUrlDiffVerb=self.mocker.responses)

    def test_register_same_verb_diff_url(self):
        bond.start_test(self)
        self.mocker.register_response(url='hi.bob', status_code='999', request_verbs=['bang'])
        self.mocker.register_response(url='hi.bill', status_code='999', request_verbs=['bang'])
        bond.spy(sameVerbDiffUrl=self.mocker.responses)

    def test_register_with_url_args(self):
        bond.start_test(self)
        self.mocker.register_response(url='https://real.com', status_code=200, request_verbs=['get'],
                                      url_params={'this': 'thing'})
        bond.spy(urlArgs=self.mocker.responses)

    def test_overload(self):
        self.mocker.register_response(url='hi.bob', status_code='999', request_verbs=['bang'])
        self.assertRaises(NotImplementedError,
                          self.mocker.register_response, url='hi.bob', status_code='777', request_verbs=['bang'])

    def test_overload_on_one_verb(self):
        self.mocker.register_response(url='hi.bob', status_code='999', request_verbs=['bang', 'boom'])
        self.assertRaises(NotImplementedError, self.mocker.register_response, url='hi.bob', status_code='777',
                          request_verbs=['bang'])

    def test_unregistered_response(self):
        bond.start_test(self)
        try:
            self.mocker.get('https://giant.balloon.com/rides', params={'time': 'now'})
        except UnregisteredURL as uu:
            bond.spy(unregistered=uu.message)

    def test_ambiguous_match(self):
        url = 'https://giant.balloon.com/rides'
        self.mocker.register_response(url=url, status_code=500, request_verbs=['get'])
        self.mocker.responses.append(self.mocker.responses[0])
        bond.start_test(self)
        try:
            self.mocker.get(url)
        except AmbiguousURLMatch as am:
            bond.spy(ambiguous_match=am.message)

    def test_same_url_diff_params_not_ambiguous(self):
        url = 'https://giant.balloon.com/rides'
        self.mocker.register_response(url=url, status_code=200, request_verbs=['get'], decoded_json={'page': '1'})
        self.mocker.register_response(url=url, status_code=200, request_verbs=['get'], url_params={'page': '2'},
                                      decoded_json={'page': '2'})
        self.mocker.register_response(url=url, status_code=200, request_verbs=['get'],
                                      url_params={'page': '3'}, decoded_json={'page': '3'})
        bond.start_test(self)
        results = list()
        results.append(self.mocker.get(url).json())
        results.append(self.mocker.get(url, params={'page': '2'}).json())
        results.append(self.mocker.get(url, params={'page': '3'}).json())
        results.append(self.mocker.get(url + '?page=2').json())
        results.append(self.mocker.get(url + '?page=3').json())
        bond.spy(url_params=results)

    def test_clear_responses(self):
        bond.start_test(self)
        self.mocker.register_response(url='hi.bob', status_code='999', request_verbs=['bang'])
        self.mocker.register_response(url='hi.bill', status_code='999', request_verbs=['bang'])
        self.mocker.clear_responses()
        bond.spy(cleared=self.mocker.responses)

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

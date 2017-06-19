from bond import bond
from response_mocker import AmbiguousURLMatch, ResponseMocker, UnregisteredURL
import unittest


class RegistrationTests(unittest.TestCase):
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
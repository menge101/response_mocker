from copy import deepcopy
from queue import Queue, Full

SUCCESS_CODES = {'get': [200, 204], 'post': [200, 201]}


class MockedResponse(object):
    """
    This is the response that is returned from the ResponseMocker.
    """
    def __init__(self, req_args, **kwargs):
        try:
            self.content = kwargs['content']
        except KeyError:
            self.content = None
        try:
            self.decoded_json = kwargs['decoded_json']
        except KeyError:
            self.decoded_json = None
        self.request = MockedRequest(kwargs['method'], kwargs['url'], req_args)
        self.status_code = kwargs['status_code']
        self.url = kwargs['url']

    def json(self):
        return self.decoded_json

    def raise_for_status(self):
        if self.status_code not in SUCCESS_CODES[self.request.method]:
            if self.status_code is 404:
                message = "{} Client Error: Not Found for url: {}".format(self.status_code, self.url)
            else:
                message = "{} Client Error: regarding url: {}".format(self.status_code, self.url)
            raise HTTPError(message, self.request, self)


class MockedRequest(object):
    """
    This is the request object that is part of the mocked response
    """
    def __init__(self, method, url, req_args):
        self.method = method
        self.url = url
        self.args = req_args


class ResponseMocker(object):
    """
    This is a 'requests' mocking class, you can preset responses to particular urls,
    which will then be returned when that url is called.
    This functionality was developed because full packages that do this kind of thing did way more than needed.

    While post functionality is available it is not as robustly developed as the get functionality.
    """
    def __init__(self, request_q_depth=1):
        self.responses = list()
        self.returned_response_q = Queue(request_q_depth)

    def clear_responses(self):
        self.responses = list()

    def get(self, url, **url_params):
        try:
            param_string = self._format_params(url_params['params'])
        except KeyError:
            param_string = ''
        return self._act(url + param_string, 'get')

    def register_response(self, **kwargs):
        if 'url' in kwargs and 'request_verbs' in kwargs and 'status_code' in kwargs:
            if 'url_params' in kwargs:
                kwargs['url'] += self._format_params(kwargs['url_params'])
                del kwargs['url_params']
            # deep copy is needed here to disconnect the stored response from objects used to create it
            self._add_response(**deepcopy(kwargs))
        else:
            raise Exception(
                ("Response registration requires keyword arguments: url (string), status_code (string), and "
                 "request_verbs (list of strings)"))

    def post(self, url, **kwargs):
        """
        This method mocks the post functionality of the requests library
        :param url: the url to post to
        :param kwargs: This is unused but is here to match the method signature to the requests library
        :return: the result
        """
        response = self._act(url, 'post', kwargs)
        return response

    def _act(self, url, verb, req_args=None):
        if req_args is None:
            req_args = dict()
        # The deepcopy here is necessary to prevent alteration of the stored response
        match = deepcopy(self._find_match(url=url, request_verb=verb))
        match['method'] = verb
        response = MockedResponse(req_args, **match)
        try:
            self.returned_response_q.put(response, block=False)
        except Full:
            self.returned_response_q.get()
            self.returned_response_q.put(response)
        return response

    def _add_response(self, **kwargs):
        for verb in kwargs['request_verbs']:
            if self._response_match(kwargs['url'], verb):
                raise NotImplementedError('Overwriting registered URLs is not implemented.')
        self.responses.append(kwargs)

    def _find_match(self, **kwargs):
        url = kwargs['url']
        verb = kwargs['request_verb']
        matches = self._find_matches(url, verb)
        if len(matches) == 1:
            match = matches.pop()
            return match
        elif len(matches) < 1:
            raise UnregisteredURL('URL: ' + url + ' not registered.')
        else:
            raise AmbiguousURLMatch('URL: ' + url + ' matches multiple results')

    def _response_match(self, url, request_verb):
        matches = self._find_matches(url, request_verb)
        return len(matches) > 0

    def _find_matches(self, url, verb):
        return self._find_verb_matches(verb, self._find_url_matches(url, self.responses))

    @staticmethod
    def _find_url_matches(url, collection):
        return filter(lambda u: url == u['url'], collection)

    @staticmethod
    def _find_verb_matches(verb, collection):
        return filter(lambda v: verb in v['request_verbs'], collection)

    @classmethod
    def _format_params(cls, arg_dict):
        kwargs_list = {cls._formatter(key, value) for (key, value) in arg_dict.items()}
        joined_list = '&'.join(kwargs_list)
        kwarg_string = '?' + joined_list
        return kwarg_string

    @classmethod
    def _formatter(cls, key, value):
        if cls._is_not_string_but_is_iterable(value):
            return cls._list_formatter(key, value)
        else:
            return cls._string_formatter(key, value)

    @staticmethod
    def _is_not_string_but_is_iterable(obj):
        return (not isinstance(obj, str)) and hasattr(obj, '__iter__')

    @classmethod
    def _list_formatter(cls, key, lst):
        return '&'.join([cls._string_formatter(key, element) for element in lst])

    @staticmethod
    def _string_formatter(key, value):
        return key + '=' + str(value)


class AmbiguousURLMatch(Exception):
    pass


class HTTPError(Exception):
    def __init__(self, msg, req, resp, *args, **kwargs):
        self.message = msg
        self.request = req
        self.response = resp
        super(HTTPError, self).__init__(args, kwargs)


class UnregisteredURL(Exception):
    pass

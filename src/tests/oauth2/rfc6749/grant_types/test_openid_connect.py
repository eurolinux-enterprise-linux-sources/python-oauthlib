# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from ....unittest import TestCase

import json
import mock
from oauthlib.common import Request
from oauthlib.oauth2.rfc6749.grant_types import OpenIDConnectAuthCode
from oauthlib.oauth2.rfc6749.grant_types import OpenIDConnectImplicit
from oauthlib.oauth2.rfc6749.grant_types import OpenIDConnectHybrid
from oauthlib.oauth2.rfc6749.grant_types import OIDCNoPrompt
from oauthlib.oauth2.rfc6749.tokens import BearerToken

from .test_authorization_code import AuthorizationCodeGrantTest
from .test_implicit import ImplicitGrantTest


class OpenIDAuthCodeInterferenceTest(AuthorizationCodeGrantTest):
    """Test that OpenID don't interfer with normal OAuth 2 flows."""

    def setUp(self):
        super(OpenIDAuthCodeInterferenceTest, self).setUp()
        self.auth = OpenIDConnectAuthCode(request_validator=self.mock_validator)

class OpenIDImplicitInterferenceTest(ImplicitGrantTest):
    """Test that OpenID don't interfer with normal OAuth 2 flows."""

    def setUp(self):
        super(OpenIDImplicitInterferenceTest, self).setUp()
        self.auth = OpenIDConnectImplicit(request_validator=self.mock_validator)


class OpenIDHybridInterferenceTest(AuthorizationCodeGrantTest):
    """Test that OpenID don't interfer with normal OAuth 2 flows."""

    def setUp(self):
        super(OpenIDHybridInterferenceTest, self).setUp()
        self.auth = OpenIDConnectHybrid(request_validator=self.mock_validator)


def get_id_token_mock(token, token_handler, request):
    return "MOCKED_TOKEN"


class OpenIDAuthCodeTest(TestCase):

    def setUp(self):
        self.request = Request('http://a.b/path')
        self.request.scopes = ('hello', 'openid')
        self.request.expires_in = 1800
        self.request.client_id = 'abcdef'
        self.request.code = '1234'
        self.request.response_type = 'code'
        self.request.grant_type = 'authorization_code'
        self.request.redirect_uri = 'https://a.b/cb'
        self.request.state = 'abc'

        self.mock_validator = mock.MagicMock()
        self.mock_validator.authenticate_client.side_effect = self.set_client
        self.mock_validator.get_id_token.side_effect = get_id_token_mock
        self.auth = OpenIDConnectAuthCode(request_validator=self.mock_validator)

        self.url_query = 'https://a.b/cb?code=abc&state=abc'
        self.url_fragment = 'https://a.b/cb#code=abc&state=abc'

    def set_client(self, request):
        request.client = mock.MagicMock()
        request.client.client_id = 'mocked'
        return True

    @mock.patch('oauthlib.common.generate_token')
    def test_authorization(self, generate_token):

        scope, info = self.auth.validate_authorization_request(self.request)

        generate_token.return_value = 'abc'
        bearer = BearerToken(self.mock_validator)
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertURLEqual(h['Location'], self.url_query)
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

    @mock.patch('oauthlib.common.generate_token')
    def test_no_prompt_authorization(self, generate_token):
        generate_token.return_value = 'abc'
        scope, info = self.auth.validate_authorization_request(self.request)
        self.request.prompt = 'none'
        self.assertRaises(OIDCNoPrompt,
                          self.auth.validate_authorization_request,
                          self.request)

        # prompt == none requires id token hint
        bearer = BearerToken(self.mock_validator)
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=invalid_request', h['Location'])
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

        self.request.id_token_hint = 'me@email.com'
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertURLEqual(h['Location'], self.url_query)
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

        # Test alernative response modes
        self.request.response_mode = 'fragment'
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertURLEqual(h['Location'], self.url_fragment, parse_fragment=True)

        # Ensure silent authentication and authorization is done
        self.mock_validator.validate_silent_login.return_value = False
        self.mock_validator.validate_silent_authorization.return_value = True
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=login_required', h['Location'])

        self.mock_validator.validate_silent_login.return_value = True
        self.mock_validator.validate_silent_authorization.return_value = False
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=consent_required', h['Location'])

        # ID token hint must match logged in user
        self.mock_validator.validate_silent_authorization.return_value = True
        self.mock_validator.validate_user_match.return_value = False
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=login_required', h['Location'])

    def set_scopes(self, client_id, code, client, request):
        request.scopes = self.request.scopes
        request.state = self.request.state
        request.user = 'bob'
        return True

    def test_create_token_response(self):
        self.request.response_type = None
        self.mock_validator.validate_code.side_effect = self.set_scopes

        bearer = BearerToken(self.mock_validator)

        h, token, s = self.auth.create_token_response(self.request, bearer)
        token = json.loads(token)
        self.assertEqual(self.mock_validator.save_token.call_count, 1)
        self.assertIn('access_token', token)
        self.assertIn('refresh_token', token)
        self.assertIn('expires_in', token)
        self.assertIn('scope', token)
        self.assertIn('id_token', token)
        self.assertIn('openid', token['scope'])

        self.mock_validator.reset_mock()

        self.request.scopes = ('hello', 'world')
        h, token, s = self.auth.create_token_response(self.request, bearer)
        token = json.loads(token)
        self.assertEqual(self.mock_validator.save_token.call_count, 1)
        self.assertIn('access_token', token)
        self.assertIn('refresh_token', token)
        self.assertIn('expires_in', token)
        self.assertIn('scope', token)
        self.assertNotIn('id_token', token)
        self.assertNotIn('openid', token['scope'])


class OpenIDImplicitTest(TestCase):

    def setUp(self):
        self.request = Request('http://a.b/path')
        self.request.scopes = ('hello', 'openid')
        self.request.expires_in = 1800
        self.request.client_id = 'abcdef'
        self.request.response_type = 'id_token token'
        self.request.redirect_uri = 'https://a.b/cb'
        self.request.nonce = 'zxc'
        self.request.state = 'abc'

        self.mock_validator = mock.MagicMock()
        self.mock_validator.get_id_token.side_effect = get_id_token_mock
        self.auth = OpenIDConnectImplicit(request_validator=self.mock_validator)

        token = 'MOCKED_TOKEN'
        self.url_query = 'https://a.b/cb?state=abc&token_type=Bearer&expires_in=3600&scope=hello+openid&access_token=abc&id_token=%s' % token
        self.url_fragment = 'https://a.b/cb#state=abc&token_type=Bearer&expires_in=3600&scope=hello+openid&access_token=abc&id_token=%s' % token

    @mock.patch('oauthlib.common.generate_token')
    def test_authorization(self, generate_token):
        scope, info = self.auth.validate_authorization_request(self.request)

        generate_token.return_value = 'abc'
        bearer = BearerToken(self.mock_validator)

        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertURLEqual(h['Location'], self.url_fragment, parse_fragment=True)
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

        self.request.response_type = 'id_token'
        token = 'MOCKED_TOKEN'
        url = 'https://a.b/cb#state=abc&id_token=%s' % token
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertURLEqual(h['Location'], url, parse_fragment=True)
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

        self.request.nonce = None
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=invalid_request', h['Location'])
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

    @mock.patch('oauthlib.common.generate_token')
    def test_no_prompt_authorization(self, generate_token):
        generate_token.return_value = 'abc'
        scope, info = self.auth.validate_authorization_request(self.request)
        self.request.prompt = 'none'
        self.assertRaises(OIDCNoPrompt,
                          self.auth.validate_authorization_request,
                          self.request)

        # prompt == none requires id token hint
        bearer = BearerToken(self.mock_validator)
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=invalid_request', h['Location'])
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

        self.request.id_token_hint = 'me@email.com'
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertURLEqual(h['Location'], self.url_fragment, parse_fragment=True)
        self.assertEqual(b, None)
        self.assertEqual(s, 302)

        # Test alernative response modes
        self.request.response_mode = 'query'
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertURLEqual(h['Location'], self.url_query)

        # Ensure silent authentication and authorization is done
        self.mock_validator.validate_silent_login.return_value = False
        self.mock_validator.validate_silent_authorization.return_value = True
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=login_required', h['Location'])

        self.mock_validator.validate_silent_login.return_value = True
        self.mock_validator.validate_silent_authorization.return_value = False
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=consent_required', h['Location'])

        # ID token hint must match logged in user
        self.mock_validator.validate_silent_authorization.return_value = True
        self.mock_validator.validate_user_match.return_value = False
        h, b, s = self.auth.create_authorization_response(self.request, bearer)
        self.assertIn('error=login_required', h['Location'])


class OpenIDHybridCodeTokenTest(OpenIDAuthCodeTest):

    def setUp(self):
        super(OpenIDHybridCodeTokenTest, self).setUp()
        self.request.response_type = 'code token'
        self.auth = OpenIDConnectHybrid(request_validator=self.mock_validator)
        self.url_query = 'https://a.b/cb?code=abc&state=abc&token_type=Bearer&expires_in=3600&scope=hello+openid&access_token=abc'
        self.url_fragment = 'https://a.b/cb#code=abc&state=abc&token_type=Bearer&expires_in=3600&scope=hello+openid&access_token=abc'

class OpenIDHybridCodeIdTokenTest(OpenIDAuthCodeTest):

    def setUp(self):
        super(OpenIDHybridCodeIdTokenTest, self).setUp()
        self.request.response_type = 'code id_token'
        self.auth = OpenIDConnectHybrid(request_validator=self.mock_validator)
        token = 'MOCKED_TOKEN'
        self.url_query = 'https://a.b/cb?code=abc&state=abc&id_token=%s' % token
        self.url_fragment = 'https://a.b/cb#code=abc&state=abc&id_token=%s' % token

class OpenIDHybridCodeIdTokenTokenTest(OpenIDAuthCodeTest):

    def setUp(self):
        super(OpenIDHybridCodeIdTokenTokenTest, self).setUp()
        self.request.response_type = 'code id_token token'
        self.auth = OpenIDConnectHybrid(request_validator=self.mock_validator)
        token = 'MOCKED_TOKEN'
        self.url_query = 'https://a.b/cb?code=abc&state=abc&token_type=Bearer&expires_in=3600&scope=hello+openid&access_token=abc&id_token=%s' % token
        self.url_fragment = 'https://a.b/cb#code=abc&state=abc&token_type=Bearer&expires_in=3600&scope=hello+openid&access_token=abc&id_token=%s' % token

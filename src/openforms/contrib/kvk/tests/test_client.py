from django.test import TestCase

import requests_mock
from requests import RequestException
from zds_client import ClientError
from zgw_consumers.test import mock_service_oas_get

from openforms.contrib.kvk.client import KVKClient
from openforms.contrib.kvk.tests.base import KVKTestMixin


class KVKClientTestCase(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_client(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=69599084",
            status_code=200,
            json=self.load_json_mock("companies.json"),
        )

        client = KVKClient()
        # exists
        res = client.query(kvkNumber=69599084)
        self.assertIsNotNone(res)
        self.assertIsNotNone(res["data"])
        self.assertIsNotNone(res["data"]["items"])
        self.assertIsNotNone(res["data"]["items"][0])
        self.assertEqual(res["data"]["items"][0]["kvkNumber"], "69599084")

    @requests_mock.Mocker()
    def test_client_404(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=69599084",
            status_code=404,
        )
        client = KVKClient()
        with self.assertRaises(ClientError):
            res = client.query(kvkNumber=69599084)

    @requests_mock.Mocker()
    def test_client_500(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=69599084",
            status_code=500,
        )
        client = KVKClient()
        with self.assertRaises(RequestException):
            res = client.query(kvkNumber=69599084)
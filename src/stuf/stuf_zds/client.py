import base64
import logging
import os
from collections import OrderedDict
from datetime import timedelta
from typing import Literal, TypedDict
from uuid import uuid4

from django.template import loader
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import requests
from defusedxml.lxml import fromstring as df_fromstring
from lxml import etree
from lxml.etree import Element
from requests import RequestException, Response

from openforms.config.models import GlobalConfiguration
from openforms.logging import logevent
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport

from ..client import BaseClient
from ..constants import STUF_ZDS_EXPIRY_MINUTES, EndpointSecurity, EndpointType
from ..models import StufService

logger = logging.getLogger(__name__)

nsmap = OrderedDict(
    (
        ("zkn", "http://www.egem.nl/StUF/sector/zkn/0310"),
        ("bg", "http://www.egem.nl/StUF/sector/bg/0310"),
        ("stuf", "http://www.egem.nl/StUF/StUF0301"),
        ("zds", "http://www.stufstandaarden.nl/koppelvlak/zds0120"),
        ("gml", "http://www.opengis.net/gml"),
        ("xsi", "http://www.w3.org/2001/XMLSchema-instance"),
        ("xmime", "http://www.w3.org/2005/05/xmlmime"),
    )
)

SCHEMA_DIR = os.path.join(
    os.path.dirname(__file__), "vendor", "Zaak_DocumentServices_1_1_02"
)
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M%S"
DATETIME_FORMAT = "%Y%m%d%H%M%S"


class PaymentStatus:
    """
    via: stuf-dms/Zaak_DocumentServices_1_1_02/zkn0310/entiteiten/zkn0310_simpleTypes.xsd

    <enumeration value="N.v.t."/>
    <enumeration value="(Nog) niet"/>
    <enumeration value="Gedeeltelijk"/>
    <enumeration value="Geheel"/>
    """

    NVT = "N.v.t."
    NOT_YET = "(Nog) niet"
    PARTIAL = "Gedeeltelijk"
    FULL = "Geheel"


def fmt_soap_datetime(d):
    return d.strftime(DATETIME_FORMAT)


def fmt_soap_date(d):
    return d.strftime(DATE_FORMAT)


def fmt_soap_time(d):
    return d.strftime(TIME_FORMAT)


def xml_value(xml, xpath, namespaces=nsmap):
    elements = xml.xpath(xpath, namespaces=namespaces)
    if len(elements) == 1:
        return elements[0].text
    else:
        raise ValueError(f"xpath not found {xpath}")


class ZaakOptions(TypedDict):
    # from stuf_zds.plugin.ZaakOptionsSerializer
    gemeentecode: str
    zds_zaaktype_code: str
    zds_zaaktype_omschrijving: str
    zds_zaaktype_status_code: str
    zds_zaaktype_status_omschrijving: str
    zds_documenttype_omschrijving_inzending: str
    zds_zaakdoc_vertrouwelijkheid: Literal[
        "ZEER GEHEIM",
        "GEHEIM",
        "CONFIDENTIEEL",
        "VERTROUWELIJK",
        "ZAAKVERTROUWELIJK",
        "INTERN",
        "BEPERKT OPENBAAR",
        "OPENBAAR",
    ]
    # extra's
    omschrijving: str
    referentienummer: str


class StufZDSClient(BaseClient):
    sector_alias = "zkn"
    sector_namespace = "http://www.egem.nl/StUF/sector/zkn/0310"
    soap_security_expires_minutes = STUF_ZDS_EXPIRY_MINUTES

    def __init__(self, service: StufService, options: ZaakOptions):
        """
        Initialize the client instance.

        :arg options: Values from the ``ZaakOptionsSerializer``, amended with
          'omschrijving' and 'referentienummer'.
        """
        super().__init__(
            service,
            request_log_hook=logevent.stuf_zds_request,
        )
        self.options = options

    def _get_request_base_context(self):
        return {
            "zender_organisatie": self.service.zender_organisatie,
            "zender_applicatie": self.service.zender_applicatie,
            "zender_gebruiker": self.service.zender_gebruiker,
            "zender_administratie": self.service.zender_administratie,
            "ontvanger_organisatie": self.service.ontvanger_organisatie,
            "ontvanger_applicatie": self.service.ontvanger_applicatie,
            "ontvanger_gebruiker": self.service.ontvanger_gebruiker,
            "ontvanger_administratie": self.service.ontvanger_administratie,
            "tijdstip_bericht": fmt_soap_datetime(timezone.now()),
            "tijdstip_registratie": fmt_soap_datetime(timezone.now()),
            "datum_vandaag": fmt_soap_date(timezone.now()),
            "gemeentecode": self.options["gemeentecode"],
            "zds_zaaktype_code": self.options["zds_zaaktype_code"],
            "zds_zaaktype_omschrijving": self.options.get("zds_zaaktype_omschrijving"),
            "zds_zaaktype_status_code": self.options.get("zds_zaaktype_status_code"),
            "zds_zaaktype_status_omschrijving": self.options.get(
                "zds_zaaktype_status_omschrijving"
            ),
            "zaak_omschrijving": self.options["omschrijving"],
            "zds_documenttype_omschrijving_inzending": self.options[
                "zds_documenttype_omschrijving_inzending"
            ],
            "zds_zaakdoc_vertrouwelijkheid": self.options[
                "zds_zaakdoc_vertrouwelijkheid"
            ],
            "referentienummer": str(uuid4()),
            "global_config": GlobalConfiguration.get_solo(),
        }

    def _wrap_soap_envelope(self, xml_str: str) -> str:
        return loader.render_to_string(
            "stuf_zds/soap/includes/envelope.xml",
            {
                "soap_version": self.service.soap_service.soap_version,
                "soap_use_wss": (
                    self.service.soap_service.endpoint_security
                    in [EndpointSecurity.wss, EndpointSecurity.wss_basicauth]
                ),
                "wss_username": self.service.soap_service.user,
                "wss_password": self.service.soap_service.password,
                "wss_created": fmt_soap_date(timezone.now()),
                "wss_expires": fmt_soap_date(
                    timezone.now() + timedelta(minutes=STUF_ZDS_EXPIRY_MINUTES)
                ),
                "content": mark_safe(xml_str),
            },
        )

    def _make_request(
        self,
        soap_action: str,
        template_name: str,
        context: dict,
        endpoint_type: str,
    ) -> tuple[Response, Element]:
        # URL for logging purposes
        _url = self.service.get_endpoint(type=endpoint_type)
        request_body = loader.render_to_string(template_name, context)
        request_data = self._wrap_soap_envelope(request_body)

        ref_nr = context["referentienummer"]
        try:
            response = self.request(
                soap_action, body=request_data, endpoint_type=endpoint_type
            )
        except RequestException as e:
            logger.error(
                "bad request for referentienummer '%s'",
                ref_nr,
                extra={"ref_nr": ref_nr},
            )
            logevent.stuf_zds_failure_response(self.service, _url)
            raise RegistrationFailed("error while making backend request") from e

        if response.status_code < 200 or response.status_code >= 400:
            error_text = parse_soap_error_text(response)
            logger.error(
                "bad response for referentienummer '%s'\n%s",
                ref_nr,
                error_text,
                extra={"ref_nr": ref_nr},
            )
            logevent.stuf_zds_failure_response(self.service, _url)
            raise RegistrationFailed(
                f"error while making backend request: HTTP {response.status_code}: {error_text}",
                response=response,
            )

        try:
            xml = df_fromstring(response.content)
        except etree.XMLSyntaxError as e:
            logevent.stuf_zds_failure_response(self.service, _url)
            raise RegistrationFailed(
                "error while parsing incoming backend response XML"
            ) from e

        logevent.stuf_zds_success_response(self.service, _url)

        return response, xml

    def create_zaak_identificatie(self) -> str:
        template = "stuf_zds/soap/genereerZaakIdentificatie.xml"
        context = self._get_request_base_context()
        _, xml = self._make_request(
            "genereerZaakIdentificatie_Di02",
            template,
            context,
            endpoint_type=EndpointType.vrije_berichten,
        )

        try:
            zaak_identificatie = xml_value(
                xml, "//zkn:zaak/zkn:identificatie", namespaces=nsmap
            )
        except ValueError as e:
            raise RegistrationFailed(
                "cannot find '/zaak/identificatie' in backend response"
            ) from e

        return zaak_identificatie

    def create_zaak(
        self, zaak_identificatie, zaak_data, extra_data, payment_required=False
    ) -> None:
        template = "stuf_zds/soap/creeerZaak.xml"
        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_identificatie,
                "extra": extra_data,
                "betalings_indicatie": (
                    PaymentStatus.NOT_YET if payment_required else PaymentStatus.NVT
                ),
            }
        )
        context.update(zaak_data)
        self._make_request(
            "creeerZaak_Lk01",
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )

    def partial_update_zaak(self, zaak_identificatie: str, zaak_data: dict) -> None:
        template = "stuf_zds/soap/updateZaak.xml"
        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_identificatie,
            }
        )
        context.update(zaak_data)
        self._make_request(
            "updateZaak_Lk01",
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )

    def set_zaak_payment(self, zaak_identificatie: str, partial: bool = False) -> dict:
        data = {
            "betalings_indicatie": PaymentStatus.PARTIAL
            if partial
            else PaymentStatus.FULL,
            "laatste_betaaldatum": fmt_soap_date(timezone.now()),
        }
        return self.partial_update_zaak(zaak_identificatie, data)

    def create_document_identificatie(self) -> str:
        template = "stuf_zds/soap/genereerDocumentIdentificatie.xml"
        context = self._get_request_base_context()
        _, xml = self._make_request(
            "genereerDocumentIdentificatie_Di02",
            template,
            context,
            endpoint_type=EndpointType.vrije_berichten,
        )

        try:
            document_identificatie = xml_value(
                xml, "//zkn:document/zkn:identificatie", namespaces=nsmap
            )
        except ValueError as e:
            raise RegistrationFailed(
                "cannot find '/document/identificatie' in backend response"
            ) from e

        return document_identificatie

    def create_zaak_document(
        self, zaak_id: str, doc_id: str, submission_report: SubmissionReport
    ) -> None:
        """
        Create a zaakdocument with the submitted data as PDF.

        NOTE: this requires that the report was generated before the submission is
        being registered. See
        :meth:`openforms.submissions.api.viewsets.SubmissionViewSet._complete` where
        celery tasks are chained to guarantee this.
        """
        template = "stuf_zds/soap/voegZaakdocumentToe.xml"

        submission_report.content.seek(0)

        base64_body = base64.b64encode(submission_report.content.read()).decode()

        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_id,
                "document_identificatie": doc_id,
                # TODO: Pass submission object, extract name.
                # "titel": name,
                "titel": "inzending",
                "auteur": "open-forms",
                "taal": "nld",
                "inhoud": base64_body,
                "status": "definitief",
                "bestandsnaam": "open-forms-inzending.pdf",
                # TODO: Use name in filename
                # "bestandsnaam": f"open-forms-{name}.pdf",
                "formaat": "application/pdf",
                "beschrijving": "Ingezonden formulier",
            }
        )

        # TODO: vertrouwelijkAanduiding

        self._make_request(
            "voegZaakdocumentToe_Lk01",
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )

    def create_zaak_attachment(
        self, zaak_id: str, doc_id: str, submission_attachment: SubmissionFileAttachment
    ) -> None:
        """
        Create a zaakdocument with the submitted file.
        """
        template = "stuf_zds/soap/voegZaakdocumentToe.xml"

        submission_attachment.content.seek(0)

        base64_body = base64.b64encode(submission_attachment.content.read()).decode()

        context = self._get_request_base_context()
        context.update(
            {
                "zaak_identificatie": zaak_id,
                "document_identificatie": doc_id,
                "titel": "bijlage",
                "auteur": "open-forms",
                "taal": "nld",
                "inhoud": base64_body,
                "status": "definitief",
                "bestandsnaam": submission_attachment.get_display_name(),
                "formaat": submission_attachment.content_type,
                "beschrijving": "Bijgevoegd document",
            }
        )

        self._make_request(
            "voegZaakdocumentToe_Lk01",
            template,
            context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )

    def check_config(self) -> None:
        url = f"{self.service.get_endpoint(EndpointType.beantwoord_vraag)}?wsdl"
        auth_kwargs = self._get_auth_kwargs()
        try:
            response = requests.get(url, **auth_kwargs)
            if not response.ok:
                error_text = parse_soap_error_text(response)
                raise InvalidPluginConfiguration(
                    f"Error while making backend request: HTTP {response.status_code}: {error_text}",
                )
        except RequestException as e:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=e)
            )


def parse_soap_error_text(response):
    """
    <?xml version='1.0' encoding='utf-8'?>
    <soap11env:Envelope xmlns:soap11env="http://www.w3.org/2003/05/soap-envelope">
      <soap11env:Body>
        <soap11env:Fault>
          <faultcode>soap11env:client</faultcode>
          <faultstring>Berichtbody is niet conform schema in sectormodel</faultstring>
          <faultactor/>
          <detail>
            <ns0:Fo02Bericht xmlns:ns0="http://www.egem.nl/StUF/StUF0301">
              <ns0:stuurgegevens>
                <ns0:berichtcode>Fo02</ns0:berichtcode>
              </ns0:stuurgegevens>
              <ns0:body>
                <ns0:code>StUF055</ns0:code>
                <ns0:plek>client</ns0:plek>
                <ns0:omschrijving>Berichtbody is niet conform schema in sectormodel</ns0:omschrijving>
                <ns0:details>:52:0:ERROR:SCHEMASV:SCHEMAV_ELEMENT_CONTENT: Element '{http://www.egem.nl/StUF/sector/zkn/0310}medewerkeridentificatie': This element is not expected. Expected is ( {http://www.egem.nl/StUF/sector/zkn/0310}identificatie ).</ns0:details>
              </ns0:body>
            </ns0:Fo02Bericht>
          </detail>
        </soap11env:Fault>
      </soap11env:Body>
    </soap11env:Envelope>
    """

    message = response.text
    if response.headers.get("content-type", "").startswith("text/html"):
        message = response.status_code
    else:
        try:
            xml = df_fromstring(response.text.encode("utf8"))
            faults = xml.xpath("//*[local-name()='Fault']", namespaces=nsmap)
            if faults:
                messages = []
                for fault in faults:
                    messages.append(
                        etree.tostring(fault, pretty_print=True, encoding="unicode")
                    )
                message = "\n".join(messages)
        except etree.XMLSyntaxError:
            pass

    return message

from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

# Namespacing in the XML we want to remove
# Note:  This could cause a collision if two of the same elements
#   are present in different namespaces
NAMESPACE_REPLACEMENTS = {
    "http://schemas.xmlsoap.org/soap/envelope/": None,
    "http://www.egem.nl/StUF/sector/bg/0310": None,
    "http://www.egem.nl/StUF/StUF0301": None,
    "http://www.w3.org/1999/xlink": None,
    "http://www.opengis.net/gml": None,
}

# StUF-BG requires some expiry time to be given so we just give it 5 minutes.
STUF_BG_EXPIRY_MINUTES = 5


class FieldChoices(DjangoChoices):
    bsn = ChoiceItem("bsn", _("BSN"))
    voornamen = ChoiceItem("voornamen", _("First Name"))
    geslachtsnaam = ChoiceItem("geslachtsnaam", _("Last Name"))
    straatnaam = ChoiceItem("straatnaam", _("Street Name"))
    huisnummer = ChoiceItem("huisnummer", _("House Number"))
    huisletter = ChoiceItem("huisletter", _("House Letter"))
    huisnummertoevoeging = ChoiceItem(
        "huisnummertoevoeging", _("House Number Addition")
    )
    postcode = ChoiceItem("postcode", _("Post Code"))
    woonplaatsNaam = ChoiceItem("woonplaatsNaam", _("Residence Name"))
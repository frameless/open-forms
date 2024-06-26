"""
Implement backend functionality for core Formio (built-in) component types.

Custom component types (defined by us or third parties) need to be organized in the
adjacent custom.py module.
"""

import logging
from datetime import time
from typing import TYPE_CHECKING, Any

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.reverse import reverse

from csp_post_processor import post_process_html
from openforms.config.constants import UploadFileType
from openforms.config.models import GlobalConfiguration
from openforms.typing import DataMapping
from openforms.utils.urls import build_absolute_uri
from openforms.validations.service import PluginValidator

from ..dynamic_config.dynamic_options import add_options_to_config
from ..formatters.formio import (
    CheckboxFormatter,
    CurrencyFormatter,
    DefaultFormatter,
    EmailFormatter,
    FileFormatter,
    NumberFormatter,
    PasswordFormatter,
    PhoneNumberFormatter,
    RadioFormatter,
    SelectBoxesFormatter,
    SelectFormatter,
    SignatureFormatter,
    TextAreaFormatter,
    TextFieldFormatter,
    TimeFormatter,
)
from ..registry import BasePlugin, register
from ..serializers import build_serializer
from ..typing import (
    Component,
    ContentComponent,
    EditGridComponent,
    FileComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
    TextFieldComponent,
)
from .translations import translate_options
from .utils import _normalize_pattern

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


logger = logging.getLogger(__name__)


@register("default")
class Default(BasePlugin):
    """
    Fallback for unregistered component types, implementing default behaviour.
    """

    formatter = DefaultFormatter


@register("textfield")
class TextField(BasePlugin[TextFieldComponent]):
    formatter = TextFieldFormatter

    def build_serializer_field(
        self, component: TextFieldComponent
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if (max_length := validate.get("maxLength")) is not None:
            extra["max_length"] = max_length

        # adding in the validator is more explicit than changing to serialiers.RegexField,
        # which essentially does the same.
        validators = []
        if pattern := validate.get("pattern"):
            validators.append(
                RegexValidator(
                    _normalize_pattern(pattern),
                    message=_("This value does not match the required pattern."),
                )
            )

        # Run plugin validators at the end after all basic checks have been performed.
        if plugin_ids := validate.get("plugins", []):
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

        if validators:
            extra["validators"] = validators

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=multiple,
            **extra,
        )
        return serializers.ListField(child=base) if multiple else base


@register("email")
class Email(BasePlugin):
    formatter = EmailFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.EmailField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if (max_length := validate.get("maxLength")) is not None:
            extra["max_length"] = max_length

        validators = []
        if plugin_ids := validate.get("plugins", []):
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

        if validators:
            extra["validators"] = validators

        base = serializers.EmailField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=multiple,
            **extra,
        )
        return serializers.ListField(child=base) if multiple else base


class FormioTimeField(serializers.TimeField):
    def validate_empty_values(self, data):
        is_empty, data = super().validate_empty_values(data)
        # base field only treats `None` as empty, but formio uses empty strings
        if data == "":
            if self.required:
                self.fail("required")
            return (True, "")
        return is_empty, data


class TimeBetweenValidator:

    def __init__(self, min_time: time, max_time: time) -> None:
        self.min_time = min_time
        self.max_time = max_time

    def __call__(self, value: time):
        # same day - straight forward comparison
        if self.min_time < self.max_time:
            if value < self.min_time:
                raise serializers.ValidationError(
                    _("Value is before minimum time"),
                    code="min_value",
                )
            if value > self.max_time:
                raise serializers.ValidationError(
                    _("Value is after maximum time"),
                    code="max_value",
                )

        # min time is on the day before the max time applies (e.g. 20:00 -> 04:00)
        else:
            if value < self.min_time and value > self.max_time:
                raise serializers.ValidationError(
                    _("Value is not between mininum and maximum time."), code="invalid"
                )


@register("time")
class Time(BasePlugin[Component]):
    formatter = TimeFormatter

    def build_serializer_field(
        self, component: Component
    ) -> FormioTimeField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        validators = []

        match (
            min_time := validate.get("minTime"),
            max_time := validate.get("maxTime"),
        ):
            case (None, None):
                pass
            case (str(), None):
                validators.append(MinValueValidator(time.fromisoformat(min_time)))
            case (None, str()):
                validators.append(MaxValueValidator(time.fromisoformat(max_time)))
            case (str(), str()):
                validators.append(
                    TimeBetweenValidator(
                        time.fromisoformat(min_time),
                        time.fromisoformat(max_time),
                    )
                )
            case _:
                logger.warning("Got unexpected min/max time in component %r", component)

        base = FormioTimeField(
            required=required,
            allow_null=not required,
            validators=validators,
        )
        return serializers.ListField(child=base) if multiple else base


@register("phoneNumber")
class PhoneNumber(BasePlugin):
    formatter = PhoneNumberFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        # maxLength because of the usage in appointments, even though our form builder
        # does not expose it. See `openforms.appointments.contrib.qmatic.constants`.
        if (max_length := validate.get("maxLength")) is not None:
            extra["max_length"] = max_length

        # adding in the validator is more explicit than changing to serialiers.RegexField,
        # which essentially does the same.
        validators = []
        if pattern := validate.get("pattern"):
            validators.append(
                RegexValidator(
                    _normalize_pattern(pattern),
                    message=_("This value does not match the required pattern."),
                )
            )

        # Run plugin validators at the end after all basic checks have been performed.
        if plugin_ids := validate.get("plugins", []):
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

        if validators:
            extra["validators"] = validators

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=multiple,
            **extra,
        )
        return serializers.ListField(child=base) if multiple else base


@register("file")
class File(BasePlugin[FileComponent]):
    formatter = FileFormatter

    @staticmethod
    def rewrite_for_request(component: FileComponent, request: Request):
        # write the upload endpoint information
        upload_endpoint = reverse("api:formio:temporary-file-upload")
        component["url"] = build_absolute_uri(upload_endpoint, request=request)

        # check if we need to apply "filePattern" modifications
        if component.get("useConfigFiletypes", False):
            config = GlobalConfiguration.get_solo()
            assert isinstance(config, GlobalConfiguration)
            mimetypes: list[str] = config.form_upload_default_file_types  # type: ignore
            component["filePattern"] = ",".join(mimetypes)
            component["file"].update(
                {
                    "allowedTypesLabels": [
                        UploadFileType(mimetype).label for mimetype in mimetypes
                    ],
                }
            )


@register("textarea")
class TextArea(BasePlugin[Component]):
    formatter = TextAreaFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if (max_length := validate.get("maxLength")) is not None:
            extra["max_length"] = max_length

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=multiple,
            **extra,
        )
        return serializers.ListField(child=base) if multiple else base


@register("number")
class Number(BasePlugin):
    formatter = NumberFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.FloatField | serializers.ListField:
        # new builder no longer exposes this, but existing forms may have multiple set
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        extra = {}
        if (max_value := validate.get("max")) is not None:
            extra["max_value"] = max_value
        if (min_value := validate.get("min")) is not None:
            extra["min_value"] = min_value

        validators = []
        if plugin_ids := validate.get("plugins", []):
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

        if validators:
            extra["validators"] = validators

        base = serializers.FloatField(
            required=required, allow_null=not required, **extra
        )
        return serializers.ListField(child=base) if multiple else base


@register("password")
class Password(BasePlugin):
    formatter = PasswordFormatter


def validate_required_checkbox(value: bool) -> None:
    """
    A required checkbox in Formio terms means it *must* be checked.
    """
    if not value:
        raise serializers.ValidationError(
            _("Checkbox must be checked."), code="invalid"
        )


@register("checkbox")
class Checkbox(BasePlugin[Component]):
    formatter = CheckboxFormatter

    def build_serializer_field(self, component: Component) -> serializers.BooleanField:
        validate = component.get("validate", {})
        required = validate.get("required", False)

        # dynamically add in more kwargs based on the component configuration
        extra = {}

        validators = []
        if required:
            validators.append(validate_required_checkbox)
        if plugin_ids := validate.get("plugins", []):
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

        if validators:
            extra["validators"] = validators

        return serializers.BooleanField(**extra)


@register("selectboxes")
class SelectBoxes(BasePlugin[SelectBoxesComponent]):
    formatter = SelectBoxesFormatter

    def mutate_config_dynamically(
        self,
        component: SelectBoxesComponent,
        submission: "Submission",
        data: DataMapping,
    ) -> None:
        add_options_to_config(component, data, submission)

    def localize(
        self, component: SelectBoxesComponent, language_code: str, enabled: bool
    ):
        if not (options := component.get("values", [])):
            return
        translate_options(options, language_code, enabled)


@register("select")
class Select(BasePlugin[SelectComponent]):
    formatter = SelectFormatter

    def mutate_config_dynamically(
        self, component, submission: "Submission", data: DataMapping
    ) -> None:
        add_options_to_config(
            component,
            data,
            submission,
            options_path="data.values",
        )

    def localize(self, component: SelectComponent, language_code: str, enabled: bool):
        if not (options := component.get("data", {}).get("values", [])):
            return
        translate_options(options, language_code, enabled)

    def build_serializer_field(
        self, component: SelectComponent
    ) -> serializers.ChoiceField:
        validate = component.get("validate", {})
        required = validate.get("required", False)
        assert "values" in component["data"]
        choices = [
            (value["value"], value["label"]) for value in component["data"]["values"]
        ]

        # map multiple false/true to the respective serializer field configuration
        field_kwargs: dict[str, Any]
        match component:
            case {"multiple": True}:
                field_cls = serializers.MultipleChoiceField
                field_kwargs = {"allow_empty": not required}
            case _:
                field_cls = serializers.ChoiceField
                field_kwargs = {}

        return field_cls(
            choices=choices,
            required=required,
            # See #4084 - form builder bug causes empty option to be added. allow_blank
            # is therefore required for select with `multiple: true` too.
            allow_blank=not required,
            **field_kwargs,
        )


@register("currency")
class Currency(BasePlugin[Component]):
    formatter = CurrencyFormatter

    def build_serializer_field(self, component: Component) -> serializers.FloatField:
        validate = component.get("validate", {})
        required = validate.get("required", False)

        extra = {}
        if (max_value := validate.get("max")) is not None:
            extra["max_value"] = max_value
        if (min_value := validate.get("min")) is not None:
            extra["min_value"] = min_value

        validators = []
        if plugin_ids := validate.get("plugins", []):
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

        if validators:
            extra["validators"] = validators

        return serializers.FloatField(
            required=required, allow_null=not required, **extra
        )


@register("radio")
class Radio(BasePlugin[RadioComponent]):
    formatter = RadioFormatter

    def mutate_config_dynamically(
        self, component: RadioComponent, submission: "Submission", data: DataMapping
    ) -> None:
        add_options_to_config(component, data, submission)

    def localize(self, component: RadioComponent, language_code: str, enabled: bool):
        if not (options := component.get("values", [])):
            return
        translate_options(options, language_code, enabled)

    def build_serializer_field(
        self, component: RadioComponent
    ) -> serializers.ChoiceField:
        """
        Convert a radio component to a serializer field.

        A radio component allows only a single value to be selected, but selecting a
        value may not be required. The available choices are taken from the ``values``
        key, which may be set dynamically (see :meth:`mutate_config_dynamically`).
        """
        validate = component.get("validate", {})
        required = validate.get("required", False)
        choices = [(value["value"], value["label"]) for value in component["values"]]
        return serializers.ChoiceField(
            choices=choices,
            required=required,
            allow_blank=not required,
            allow_null=not required,
        )


@register("signature")
class Signature(BasePlugin[Component]):
    formatter = SignatureFormatter

    def build_serializer_field(self, component: Component) -> serializers.CharField:
        validate = component.get("validate", {})
        required = validate.get("required", False)
        return serializers.CharField(required=required, allow_blank=not required)


@register("content")
class Content(BasePlugin):
    """
    Formio's WYSIWYG component.
    """

    # not really relevant as content components don't have values
    formatter = DefaultFormatter

    @staticmethod
    def rewrite_for_request(component: ContentComponent, request: Request):
        """
        Ensure that the inline styles are made compatible with Content-Security-Policy.

        .. note:: we apply Bleach and a CSS declaration allowlist as part of the
           post-processor because content components are not purely "trusted" content
           from form-designers, but can contain malicious user input if the form
           designer uses variables inside the HTML. The form submission data is passed
           as template context to these HTML blobs, posing a potential injection
           security risk.
        """
        component["html"] = post_process_html(component["html"], request)


@register("editgrid")
class EditGrid(BasePlugin[EditGridComponent]):
    def build_serializer_field(
        self, component: EditGridComponent
    ) -> serializers.ListField:
        validate = component.get("validate", {})
        required = validate.get("required", False)
        nested = build_serializer(
            components=component.get("components", []),
            # XXX: check out type annotations here, there's some co/contra variance
            # in play
            register=self.registry,
        )
        kwargs = {}
        if (max_length := validate.get("maxLength")) is not None:
            kwargs["max_length"] = max_length
        return serializers.ListField(
            child=nested,
            required=required,
            allow_null=not required,
            allow_empty=not required,
            **kwargs,
        )

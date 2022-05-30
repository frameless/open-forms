import factory

from openforms.products.tests.factories import ProductFactory

from ...formio.utils import is_layout_component, iter_components
from ..constants import FormVariableDataTypes, FormVariableSources
from ..models import Form, FormDefinition, FormStep, FormVariable, FormVersion
from ..utils import form_to_json


class FormFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Form %03d" % n)
    slug = factory.Faker("word")
    active = True
    product = factory.SubFactory(ProductFactory)
    payment_backend = ""
    # factory-boy ignores attributes starting with an underscore so we'll use Meta.rename
    deleted_ = False

    class Meta:
        model = Form
        rename = {"deleted_": "_is_deleted"}

    class Params:
        generate_minimal_setup = factory.Trait(
            formstep=factory.RelatedFactory(
                "openforms.forms.tests.factories.FormStepFactory",
                factory_related_name="form",
            ),
        )


class FormDefinitionFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "FormDefinition %03d" % n)

    slug = factory.Sequence(lambda n: f"fd-{n}")
    login_required = False
    configuration = {"components": [{"type": "test-component", "key": "test-key"}]}

    class Meta:
        model = FormDefinition

    class Params:
        is_appointment = factory.Trait(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                    {
                        "key": "lastName",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                ],
            }
        )


class FormStepFactory(factory.django.DjangoModelFactory):
    form_definition = factory.SubFactory(FormDefinitionFactory)
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = FormStep

    @classmethod
    def create_with_variables(
        cls,
        **kwargs,
    ) -> FormStep:
        form_step = cls.create(**kwargs)

        form_definition_configuration = form_step.form_definition.configuration
        for component in iter_components(
            configuration=form_definition_configuration, recursive=True
        ):
            if is_layout_component(component):
                continue

            FormVariableFactory.create(
                form=form_step.form,
                form_definition=form_step.form_definition,
                key=component["key"],
                is_sensitive_data=component.get("isSensitiveData", False),
            )

        return form_step


class FormVersionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    export_blob = {}

    class Meta:
        model = FormVersion

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        json_form = form_to_json(obj.form.id)
        obj.export_blob = json_form
        obj.save()


class FormPriceLogicFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    json_logic_trigger = {"==": [{"var": "test-key"}, 1]}
    price = factory.Faker(
        "pydecimal",
        left_digits=2,
        right_digits=2,
        positive=True,
        min_value=5.00,
        max_value=100.00,
    )

    class Meta:
        model = "forms.FormPriceLogic"


class FormVariableFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Variable %03d" % n)
    form = factory.SubFactory(FormFactory)
    key = factory.Faker("word")
    form_definition = factory.SubFactory(FormDefinitionFactory)
    source = FormVariableSources.user_defined
    data_type = FormVariableDataTypes.string
    initial_value = {}

    class Meta:
        model = FormVariable

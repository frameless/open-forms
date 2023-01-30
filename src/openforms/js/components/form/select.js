import {Formio} from 'formiojs';

import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {localiseSchema} from './i18n';

const Select = Formio.Components.components.select;

const optionsChoices = [
  {
    type: 'select',
    key: 'openForms.dataSrc',
    label: 'Data source',
    description: 'What data to use for the options of this field.',
    defaultValue: 'manual',
    data: {
      values: [
        {
          label: 'Manually fill in',
          value: 'manual',
        },
        {
          label: 'Variable',
          value: 'variable',
        },
      ],
    },
    validate: {
      required: true,
    },
  },
  {
    type: 'datagrid',
    input: true,
    label: 'Values',
    key: 'data.values',
    tooltip:
      'The values that can be picked for this field. Values are text submitted with the form data. ' +
      'Labels are text that appears next to the radio buttons on the form.',
    weight: 10,
    reorder: true,
    defaultValue: [{label: '', value: ''}],
    components: [
      {
        label: 'Label',
        key: 'label',
        input: true,
        type: 'textfield',
      },
      {
        label: 'Value',
        key: 'value',
        input: true,
        type: 'textfield',
        allowCalculateOverride: true,
        calculateValue: {_camelCase: [{var: 'row.label'}]},
        validate: {
          required: true,
        },
      },
    ],
    conditional: {
      show: true,
      when: 'openForms.dataSrc',
      eq: 'manual',
    },
  },
  {
    label: 'Default Value',
    key: 'defaultValue',
    tooltip: 'This will be the initial value for this field, before user interaction.',
    input: true,
    conditional: {
      show: true,
      when: 'openForms.dataSrc',
      eq: 'manual',
    },
  },
  {
    label: 'Items',
    key: 'openForms.itemsExpression',
    type: 'textarea',
    tooltip:
      'A JSON logic expression returning a variable (of array type) whose items should be used as the options for this component.',
    editor: 'ace',
    as: 'json',
    // Documentation for editor settings: https://ajaxorg.github.io/ace-api-docs/interfaces/Ace.EditorOptions.html
    // but most of the settings don't seem to work.
    conditional: {
      show: true,
      when: 'openForms.dataSrc',
      eq: 'variable',
    },
    validate: {
      required: true,
    },
  },
  {
    label: 'Items value',
    key: 'openForms.valueExpression',
    type: 'textarea',
    tooltip:
      'In case the items are objects, provide a JSON logic expression to construct the value to use from each item of the array. ' +
      'For example, this is needed when referring to repeating groups.',
    editor: 'ace',
    as: 'json',
    conditional: {
      show: true,
      when: 'openForms.dataSrc',
      eq: 'variable',
    },
  },
];

class SelectField extends Select {
  static schema(...extend) {
    return localiseSchema({...Select.schema(...extend), key: 'select-key'});
  }

  static get builderInfo() {
    return {
      ...Select.builderInfo,
      schema: SelectField.schema(),
    };
  }

  static editForm() {
    const BASIC_TAB = {
      ...BASIC,
      components: [...BASIC.components, ...optionsChoices],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default SelectField;

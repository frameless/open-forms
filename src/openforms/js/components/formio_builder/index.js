import BEM from 'bem.js';
import flatpickr from 'flatpickr';
import {Dutch} from 'flatpickr/dist/l10n/nl.js';
import React from 'react';
import ReactDOM from 'react-dom';

import {
  clearObsoleteLiterals,
  persistComponentTranslations,
} from 'components/formio_builder/translation';
import {onLoaded} from 'utils/dom';

import FormIOBuilder from './builder';

/** @const {string} The form builder block name. */
export const BLOCK_FORM_BUILDER = 'form-builder';

/** @const {string} The container element to render Formio on. */
export const ELEMENT_CONTAINER = 'container';

onLoaded(() => {
  const FORM_BUILDERS = BEM.getBEMNodes(BLOCK_FORM_BUILDER);
  [...FORM_BUILDERS].forEach(node => {
    const configurationInput = BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, 'configuration-input');
    const componentTranslationsInput = BEM.getChildBEMNode(
      node.closest('form'),
      BLOCK_FORM_BUILDER,
      'component-translations'
    );

    const configuration = JSON.parse(configurationInput.value) || {display: 'form'};
    let componentTranslations = JSON.parse(componentTranslationsInput.value) || {};

    const onChange = newConfiguration => {
      // extract translations
      configurationInput.value = JSON.stringify(newConfiguration);
    };

    /**
     * Update the translations store when a component is altered.
     */
    const onComponentMutated = (mutationType, schema, ...rest) => {
      let configuration;

      switch (mutationType) {
        case 'changed': {
          configuration = rest[1];
          break;
        }
        case 'removed': {
          configuration = rest[0];
          break;
        }
        default:
          throw new Error(`Unknown mutation type '${mutationType}'`);
      }

      persistComponentTranslations(componentTranslations, schema);
      componentTranslations = clearObsoleteLiterals(componentTranslations, configuration);
      componentTranslationsInput.value = JSON.stringify(componentTranslations);
    };

    ReactDOM.render(
      <FormIOBuilder
        configuration={configuration}
        onChange={onChange}
        onComponentMutated={onComponentMutated}
        componentTranslations={componentTranslations}
      />,
      BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, ELEMENT_CONTAINER)
    );
  });

  initFlatpickr();
});

const initFlatpickr = () => {
  flatpickr.localize(Dutch);
};

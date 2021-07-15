import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';

import FAIcon from '../FAIcon';
import FormModal from '../FormModal';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Select from '../forms/Select';
import SubmitRow from "../forms/SubmitRow";
import { FormDefinitionsContext } from './Context';
import { getFormDefinitionChoices } from './utils';


const NewStepFormDefinitionPicker = ({ onReplace }) => {
    const formDefinitions = useContext(FormDefinitionsContext);
    const formDefinitionChoices = getFormDefinitionChoices(formDefinitions);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedFormDefinition, setSelectedFormDefinition] = useState('');
    const [validationErrors, setValidationErrors] = useState([]);

    const closeModal = () => {
        setIsModalOpen(false);
    };

    const onFormDefinitionConfirmed = () => {
        if (!selectedFormDefinition) {
            setValidationErrors(['Dit veld is verplicht.']);
        } else {
            closeModal();
            onReplace(selectedFormDefinition);
        }
    };

    const onSelectChange = (event) => {
        const { target: {value} } = event;
        setValidationErrors([]);
        setSelectedFormDefinition(value);
    };

    return (
        <div className="tiles tiles--horizontal">
            <button type="button" className="tiles__tile" onClick={() => setIsModalOpen(true)}>
                <FAIcon icon="recycle" extraClassname="fa-2x" title="Selecteer definitie" />
                <span>Gebruik bestaande formulierdefinitie</span>
            </button>

            <span className="tiles__separator">&bull;</span>

            <button type="button" className="tiles__tile" onClick={() => {onReplace('')}}>
                <FAIcon icon="pencil-square-o" extraClassname="fa-2x" title="Maak definitie" />
                <span>Maak een nieuwe formulierdefinitie</span>
            </button>

            <FormModal
                isOpen={isModalOpen}
                closeModal={closeModal}
                title="Gebruik bestaande formulierdefinitie"
            >
                <FormRow>
                    <Field
                        name="form-definition"
                        label="Selecteer formulierdefinitie"
                        errors={validationErrors}
                        required
                    >
                        <Select
                            name="Form definition"
                            choices={formDefinitionChoices}
                            value={selectedFormDefinition}
                            onChange={onSelectChange}
                        />
                    </Field>
                </FormRow>

                <SubmitRow onSubmit={onFormDefinitionConfirmed} btnText="Bevestigen" isDefault preventDefault />
            </FormModal>

        </div>
    );
};

NewStepFormDefinitionPicker.propTypes = {
    onReplace: PropTypes.func.isRequired,
};

export default NewStepFormDefinitionPicker;
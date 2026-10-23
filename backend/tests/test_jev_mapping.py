from types import SimpleNamespace

import pytest

from app.services.jev_mapping import eligible


@pytest.mark.parametrize('label', ['Visa sponsorship', 'Age', 'Date of birth', 'Gender identity',
    'I agree to privacy terms', 'Race or ethnicity', 'Do you have a disability?', 'National origin',
    'Provide your phone and certify you are authorized'])
def test_sensitive_controls_excluded_in_code(label):
    field = SimpleNamespace(normalized_intent='custom', input_type='text', label=label, options=[])
    assert not eligible(field)


@pytest.mark.parametrize('label', ['Do you hold a work permit?', 'What is your desired pay?', 'Are you legally allowed to work here?'])
def test_legal_and_pay_questions_are_excluded(label):
    field = SimpleNamespace(normalized_intent='custom', input_type='text', label=label, options=[])
    assert not eligible(field)


@pytest.mark.parametrize('label', ['Personal webpage', 'International contact number'])
def test_benign_contact_labels_are_not_substring_excluded(label):
    field = SimpleNamespace(normalized_intent='custom', input_type='text', label=label, options=[])
    assert eligible(field)


def test_checkbox_and_sensitive_options_are_never_sent():
    field = SimpleNamespace(normalized_intent='custom', input_type='checkbox', label='Your information', options=[])
    assert not eligible(field)
    field.input_type = 'select'
    field.options = [{'value': 'visa', 'label': 'Visa sponsorship'}]
    assert not eligible(field)

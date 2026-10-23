"""Public employer query variants stay exactly pinned and posting-bound."""
import copy
import os
from types import SimpleNamespace
import pytest

from app.adapters.ashby_hosted import public_read
from app.adapters.ashby_queries import PUBLIC_QUERIES, PUBLIC_QUERY_VARIANTS

URL = 'https://jobs.ashbyhq.com/10xteam/24572aaa-7703-4cee-ac6b-54cf863dbe12/application'


def request(query):
    return SimpleNamespace(method='POST', url='https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting',
                           post_data_json=dict(operationName='ApiJobPosting', query=query,
                              variables=dict(organizationHostedJobsPageName='10xteam', jobPostingId=URL.split('/')[-2])))


def test_equivalent_observed_public_detail_fragment_query_loads_form():
    assert public_read(request(PUBLIC_QUERIES['ApiJobPosting']), URL)
    assert public_read(request(PUBLIC_QUERY_VARIANTS['ApiJobPosting'][0]), URL)


def test_variant_permission_rejects_other_posting_company_fields_or_payloads():
    original = request(PUBLIC_QUERY_VARIANTS['ApiJobPosting'][0])
    altered = []
    for variable, value in [('jobPostingId', 'other-posting'), ('organizationHostedJobsPageName', 'other-company'), ('candidateEmail', 'synthetic@example.invalid')]:
        current = copy.deepcopy(original)
        current.post_data_json['variables'][variable] = value
        altered.append(current)
    current = copy.deepcopy(original)
    current.post_data_json['query'] += '\nquery UnapprovedRead { candidate { email } }'
    altered.append(current)
    current = copy.deepcopy(original)
    current.post_data_json['unapproved'] = True
    altered.append(current)
    current = copy.deepcopy(original)
    current.url += '&extra=1'
    altered.append(current)
    assert all(not public_read(current, URL) for current in altered)


@pytest.mark.skipif(os.environ.get('TURIO_BROWSER_TESTS') != '1', reason='Isolated Chromium fixture.')
async def test_required_hosted_url_question_can_use_reviewed_scalar_transport():
    from playwright.async_api import async_playwright
    from app.adapters import ashby_hosted
    async with async_playwright() as driver:
        browser = await driver.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content('<div data-field-path="linkedin"><label>LinkedIn URL</label><input type="url"></div>')
            page._turio_hosted_form = {'_turio_form_controls': [{'definition_id': 'public-fixture', 'controls': [{'identifier': 'nonce', 'title': 'Submit'}]}],
                'sections': [{'fieldEntries': [{'field': {'path': 'linkedin', 'title': 'LinkedIn URL', 'type': 'Url'}, 'isRequired': True}]}]}
            schema = await ashby_hosted.schema(page)
            assert schema['manual_submission_required'] is False
            assert schema['fields'][0]['input_type'] == 'url' and schema['fields'][0]['rpc_supported']
        finally:
            await browser.close()


def test_hosted_url_value_remains_exact_reviewed_text_and_rejects_objects():
    from app.adapters.hosted_submission import scalar_value
    from app.core.errors import AppError
    value = 'https://www.linkedin.com/in/synthetic'
    assert scalar_value({'hosted_type': 'Url'}, value) == value
    with pytest.raises(AppError):
        scalar_value({'hosted_type': 'Url'}, {'unapproved': value})

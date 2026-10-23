// Node 23.6+ strips erasable TypeScript directly; no compiler API or dependency needed.
const assert = require('node:assert/strict');
const { automaticBlocker, approvalFingerprint, batchApprovalFresh, filledValue } = require('../frontend/lib/bulk.ts');
const ready = { id: 'application', job: { id: 'job', title: 'Engineer', company: 'Synthetic Company' }, application_url: 'https://employer.invalid', resume_id: 'resume', profile_version: 3,
  status: 'ready_for_review', manual_submission_required: false, missing_fields: [],
  fields: [{ field_key: 'name', label: 'Name', input_type: 'text', required: true, options: [],
    value: 'Synthetic Candidate', value_source: 'profile', user_confirmed: true }] };
assert.equal(automaticBlocker(ready), null);
assert.ok(automaticBlocker({ ...ready, manual_submission_required: true }));
assert.ok(automaticBlocker({ ...ready, manual_submission_required: undefined }));
assert.ok(automaticBlocker({ ...ready, status: 'submitted' }));
assert.ok(automaticBlocker({ ...ready, fields: [{ ...ready.fields[0], user_confirmed: false, value_source: 'jev_profile' }] }));
assert.ok(automaticBlocker({ ...ready, fields: [{ ...ready.fields[0], input_type: 'checkbox', value: false }] }));
for (const change of [{ id: 'other-application' }, { job: { ...ready.job, title: 'Changed role' } }, { job: { ...ready.job, company: 'Changed employer' } }, { resume_id: 'other' }, { profile_version: 4 }, { application_url: 'https://other.invalid' },
  { fields: [{ ...ready.fields[0], value: 'Changed Candidate' }] },
  { fields: [{ ...ready.fields[0], label: 'Changed employer question' }] }]) {
  assert.notEqual(approvalFingerprint(ready), approvalFingerprint({ ...ready, ...change }));
}
assert.equal(approvalFingerprint(ready), approvalFingerprint({ ...ready, review_token: 'a'.repeat(64), revision: 10 }));
assert.equal(batchApprovalFresh(1000, 1000 + 15 * 60 * 1000), true);
assert.equal(batchApprovalFresh(1000, 1000 + 15 * 60 * 1000 + 1), false);
assert.equal(batchApprovalFresh(1000, 999), false);
assert.equal(filledValue({ value: false }), 'No');
assert.equal(filledValue({ value: 'resume', input_type: 'file' }), 'Stored original resume');
assert.equal(filledValue({ value: 'us', input_type: 'select', options: [{ value: 'us', label: 'United States' }] }), 'United States');
console.log('PASS: bulk eligibility, immutable approval binding and field display checks');

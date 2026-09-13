# Turio — Project Specification

## 1. Problem

Job seekers repeatedly search for suitable roles, interpret job requirements, and complete repetitive applications. Turio aims to reduce this manual work while keeping the user in control.

## 2. Proposed solution

Turio provides one integrated workflow:

```text
Resume analysis
→ Candidate profile
→ Job discovery
→ Semantic matching
→ Ranking
→ Explainable recommendations
→ Application preparation
→ Browser-assisted application
→ Tracking
```

This integrated workflow is the documented research gap: existing work addresses semantic matching, recommender systems, career planning, and application support separately, while Turio aims to combine them.

## 3. Functional requirements

### FR-01 Resume upload
The user can upload a supported resume document.

### FR-02 Resume extraction
Extract relevant resume content and structure.

### FR-03 Candidate profile
Create a persistent structured profile containing, when available:

- full name
- email
- phone
- location
- skills
- education
- experience
- projects
- preferred roles
- LinkedIn
- GitHub
- portfolio
- resume file reference
- verified application preferences

### FR-04 Job ingestion
Import jobs from the selected dataset/source and normalize them.

### FR-05 Semantic matching
Use Sentence-BERT/Sentence Transformers to compare candidate/job representations.

### FR-06 Structured filtering
Support criteria such as:

- skills
- education
- experience
- location
- user preferences

### FR-07 Ranking
Produce an ordered set of job recommendations.

### FR-08 Explanation
Provide a grounded explanation of why a job matches.

### FR-09 Application analysis
Inspect a supported application form and identify fields/questions.

### FR-10 Profile-to-form mapping
Map application fields to verified candidate data.

### FR-11 Missing-information collection
Ask only for information not already stored and required to continue.

### FR-12 Custom question assistance
For genuinely generative questions, create a draft that the user can review/edit.

### FR-13 Browser-assisted filling
Fill supported fields and upload the user's stored resume.

### FR-14 Human review
Show the completed application before final submission.

### FR-15 User-approved submission
Only submit after explicit approval.

### FR-16 Tracking
Store company, job, application date, status, URL, and outcome/notes.

## 4. Research requirements

Coordinator-required additions:

- multimodal fusion for improved job matching,
- edge optimization for real-time application assistance,
- original data-driven evaluation methodology.

These are not optional future ideas; they are part of the required final project scope.

## 5. Non-functional requirements

- Accuracy: field mapping and resume extraction must be testable.
- Reliability: browser automation must use bounded retries.
- Explainability: recommendations must be traceable to stored matching factors.
- Privacy: user documents and profile information require controlled storage/access.
- Reproducibility: experiments must use fixed datasets/configurations and logged versions.
- Maintainability: website-specific automation must be isolated behind adapters.
- Efficiency: expensive AI operations should be cached and batched.

## 6. Initial supported application sites

Initial trial:

- 1Password / Ashby
- Linear / Ashby
- Supabase / Ashby
- Vercel / Ashby
- Notion / Ashby

Support means the actual application workflow has been tested, not simply that the company uses Ashby.

## 7. Out of scope for initial MVP

- unrestricted support for every company/ATS,
- blind auto-submission,
- bypassing CAPTCHA or security controls,
- fabricating user answers,
- automatic hiring decisions,
- recruiter-side candidate selection.

## 8. Acceptance definition

The MVP must demonstrate:

1. resume upload,
2. structured profile creation,
3. job ingestion,
4. semantic matching,
5. ranking,
6. explanation,
7. at least one working supported application flow,
8. profile-based automatic form filling,
9. missing-data handling,
10. user review,
11. application tracking,
12. measurable evaluation.

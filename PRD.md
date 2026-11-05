# AI Customer Support Email Agent

## 1. Product summary

Build a web application that connects to a support Gmail inbox, finds incoming
messages that need a response, retrieves relevant information from a team
knowledge base, and prepares a context-grounded reply with Google Gemini. The
user can review, edit, approve, and send each reply from the application.

The initial release is review-first: it does not send an AI-generated message
without an explicit user action. A later, separately enabled automation mode
may send replies automatically under configurable rules.

## 2. Problem

Support teams spend time reading repetitive messages, searching for policy or
product information, and writing similar answers. This creates slow response
times and inconsistent answers. A useful assistant should reduce that work
without inventing policy, exposing private information, or sending an
unreviewed response by default.

## 3. Goals and success measures

### Goals

- Connect to a Gmail mailbox with the minimum permissions needed.
- Identify and display new, unanswered incoming messages.
- Index approved knowledge-base content with Mistral embeddings.
- Retrieve relevant content and use it to draft a helpful answer with Gemini.
- Let a user review, edit, approve, send, dismiss, or retry a draft.
- Keep a trace of message status and the knowledge sources used for a draft.

### MVP measures

- Every reply is linked to its source email and displayed supporting sources.
- No AI-generated reply is sent without a human approval action.
- Users can distinguish a draft from a sent reply and see failures clearly.
- Evaluate answer usefulness, groundedness, and handling of unanswerable
  questions on a representative set of support emails before launch.

## 4. Users

- **Support agent:** reviews incoming email, edits and sends suggested replies.
- **Workspace administrator:** connects the mailbox, manages knowledge sources,
  and configures model and automation settings.

## 5. User scenario and workflow

1. An administrator signs in to the application and connects a Google account
   using Google's OAuth consent flow.
2. The backend checks the configured Gmail inbox for new messages (polling is
   the MVP approach). It ignores messages sent by the connected account and
   avoids processing the same message more than once.
3. The agent sees a queue containing the sender, subject, received time, status,
   and a safe preview of each message.
4. The agent opens a message. The backend extracts its readable text, searches
   the indexed knowledge base using a Mistral embedding, and sends the relevant
   excerpts and message context to Gemini to draft a response.
5. The application shows the proposed response, retrieved knowledge sources,
   and any uncertainty or missing information.
6. The agent edits and sends the reply, asks for a new draft, or dismisses it.
   The backend sends approved replies through the Gmail API and records the
   result.
7. If the knowledge base does not support a reliable answer, the assistant
   says so and asks the agent to handle the message; it must not fabricate a
   policy or promise.

## 6. Functional requirements

### Gmail connection and inbox

- Use Google OAuth 2.0 for mailbox access. A Gmail API key alone does not grant
  access to private mail or permission to send mail.
- Request only the Gmail scopes required by enabled features. Inbox reading and
  sending require appropriate OAuth scopes and may require Google verification
  depending on deployment and audience.
- Store OAuth refresh tokens securely; never expose tokens or provider keys to
  the browser or log them.
- List incoming messages, load message details and thread context, and track
  processing and reply status.
- Support pagination, retries for transient errors, and Gmail API quota limits.
- Prevent duplicate drafts and replies when an email is polled or retried.

### Knowledge base and retrieval

- Allow administrators to add, replace, and remove supported documents.
- MVP document formats: PDF, DOCX, and plain text/Markdown; enforce upload
  limits and validate file type and content.
- Extract and chunk text, create embeddings with the configured Mistral
  embedding model, and store vectors with source metadata.
- Retrieve relevant chunks for a message and show source names (and page or
  section where available) with the draft.
- Provide a way to re-index content after a document or embedding-model change.
- Treat retrieved document text as untrusted reference material, not as
  instructions that can override system rules.

### Drafting and review

- Use Gemini to draft concise, professional responses based on the email and
  retrieved knowledge. Do not claim facts unsupported by the retrieved content.
- Include relevant thread context while excluding unrelated messages.
- Show the draft, its supporting sources, generation status, and errors.
- Allow editing, regeneration, dismissal, and explicit approval to send.
- Support a configurable signature and tone without allowing these settings to
  override safety and grounding requirements.
- Do not automatically reply to spam, bulk mail, out-of-office messages, or
  messages the configured rules exclude.

### Automation (post-MVP, disabled by default)

- Automatic sending must require explicit administrator opt-in and must be
  visibly distinguishable from review-first operation.
- Provide sender/domain, confidence, and message-type allow/deny rules, a
  maximum-send rate, a pause/kill switch, and an audit trail.
- Route uncertain, unsupported, sensitive, or policy-exception messages to
  human review.
- Test automation in draft-only/shadow mode before enabling sending.

## 7. Non-functional requirements

- **Security:** use HTTPS in deployment, secure secrets and OAuth tokens, apply
  least-privilege access, and redact sensitive message content from logs.
- **Privacy:** make data retention configurable; provide deletion of mailbox
  records, uploaded documents, and their embeddings. Do not use customer email
  to train models unless separately and explicitly authorized.
- **Reliability:** use idempotent message processing, bounded retries, and
  visible failure states; do not silently mark failed sends as successful.
- **Performance:** show inbox and draft progress promptly; use asynchronous
  work for provider calls and document indexing.
- **Observability:** record operational events and provider errors without
  logging message bodies, credentials, or tokens.
- **Accessibility:** ensure the review queue and draft actions are keyboard
  accessible and have clear status labels.

## 8. Proposed technology stack

- **Backend:** Python 3.14 (matching the current `pyproject.toml` minimum),
  FastAPI, Pydantic settings, SQLAlchemy, and Alembic.
- **Frontend:** Node.js with a JavaScript/TypeScript framework (React is a
  reasonable starting choice), calling the backend over a REST API. Frontend
  dependencies belong in `package.json`, not `requirements.txt`.
- **Email:** Gmail API via `google-api-python-client` and Google OAuth libraries.
- **Drafting:** Google Gen AI SDK (`google-genai`) with a configurable Gemini
  model.
- **Embeddings:** Mistral SDK (`mistralai`) with a configurable embedding model.
- **Storage:** PostgreSQL for application data in production; SQLite may be
  used for local development. Chroma is the proposed vector store for the MVP;
  evaluate a managed or self-hosted alternative as scale and deployment needs
  become clear.
- **Document processing:** Python libraries for PDF, DOCX, and text uploads.

Model names, OAuth settings, database URLs, polling interval, upload limits, and
allowed auto-send rules must be configuration, not hard-coded assumptions.

## 9. Core data

- **Mailbox connection:** Google account identifier, granted scopes, encrypted
  refresh token, connection state.
- **Email:** Gmail message/thread IDs, sender and recipient metadata, subject,
  received time, processing status, and required message content.
- **Draft:** generated text, edited text, model metadata, status, timestamps,
  and send result.
- **Knowledge source:** document metadata, extracted chunks, embedding
  references, indexing state, and source locations.
- **Audit event:** actor, action, affected record, timestamp, and outcome;
  avoid storing unnecessary message content in audit records.

## 10. Risks and mitigations

| Risk or challenge | Mitigation |
|---|---|
| Gmail API keys cannot authorize private inbox access | Use OAuth 2.0; request and explain the minimum necessary scopes. |
| Google OAuth verification or consent-screen restrictions delay launch | Decide early whether the app is internal or public; follow Google's current verification requirements. |
| AI produces incorrect or overconfident answers | Ground drafts in retrieved sources, surface those sources, abstain when unsupported, and require review in the MVP. |
| Prompt injection appears in email or uploaded documents | Treat all message and document text as untrusted data; do not follow embedded instructions or expose secrets. |
| Sensitive customer data is sent to external model providers | Disclose provider processing, minimize submitted context, review provider retention/terms, and configure retention appropriately. |
| Gmail quota limits, transient errors, or token revocation interrupt processing | Use backoff, quota-aware polling, token refresh handling, and clear reconnect/error states. |
| Duplicate or threaded emails cause duplicate replies | Use Gmail IDs and idempotency checks; track thread and send states. |
| Poor or outdated knowledge creates misleading drafts | Show source and freshness information, support re-indexing, and route weak retrieval to review. |
| Malformed or oversized uploads cause failures or abuse | Validate formats, cap upload and extracted-text size, and handle parsing failures visibly. |
| Automated replies reach the wrong sender or create loops | Keep auto-send off by default; exclude self, bulk, bounce, and out-of-office messages; enforce allow/deny rules and a kill switch. |
| Vector index and source documents become inconsistent | Track indexing state and source versions; support re-indexing and deletion across both stores. |

## 11. Out of scope for the MVP

- Sending replies automatically without a separate opt-in and safety controls.
- Supporting providers other than Gmail.
- Complex ticket routing, CRM synchronization, analytics dashboards, or
  multi-tenant billing.
- Training or fine-tuning a model on customer messages.

## 12. Delivery stages

1. **Foundation:** configuration/secrets, database models, OAuth connection, and
   basic Gmail inbox listing.
2. **Knowledge and drafting:** document ingestion, Mistral embeddings,
   retrieval, Gemini drafts, and source display.
3. **Review and send:** queue and editor UI, approval workflow, Gmail sending,
   status tracking, and audit events.
4. **Hardening:** error handling, privacy/retention controls, tests, quota and
   security checks, and evaluation against representative support messages.
5. **Optional automation:** shadow mode, administrator controls, policy
   safeguards, and a gradual opt-in rollout.

## 13. MVP acceptance criteria

- An administrator can connect and disconnect a Gmail account through OAuth.
- New incoming messages appear once in the application and can be opened.
- An administrator can upload supported knowledge documents and see indexing
  success or a useful error.
- A draft uses retrieved knowledge, identifies its sources, and handles
  insufficient evidence by asking for human review.
- A user can edit and explicitly send a draft; sending failures are visible and
  do not create a false success state.
- No draft is auto-sent in the MVP.
- Provider credentials and OAuth tokens are not present in frontend code,
  source control, or application logs.
- Tests cover message deduplication, retrieval/draft flow, unsupported
  questions, approval-before-send, and provider/API failure handling.
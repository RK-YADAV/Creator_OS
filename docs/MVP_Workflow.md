# Creator_OS MVP Workflow

## 1. MVP objective

Creator_OS should prove one focused hypothesis:

> A creator is more likely to accept an AI-generated draft when the system checks it against the creator's published archive and the original source before asking for approval.

The MVP should support one real creator, one source type, and one publishing channel. The source can be an MP4 recording that is converted into a traceable transcript. A recommended first slice is:

```text
MP4 video -> transcript with timestamps -> LinkedIn post -> creator review -> feedback memory
```

The system is not an autonomous publisher. It prepares, checks, and explains a draft. The creator makes the final decision.

## 2. End-to-end workflow

### Step 1: Configure the creator

The creator or operator imports at least 20 published pieces and records:

- Creator name and channel
- Preferred post length
- Topics or themes
- Optional words and styles to avoid

Each archive item should retain its source text, publication date, URL if available, and basic metadata.

### Step 2: Ingest raw material

The creator uploads one MP4 video. The system validates the file before processing:

- File extension and MIME type are both `video/mp4`
- File is within the configured size and duration limits
- Video contains an audio track
- The upload completed successfully and can be read

The original MP4 is stored as an immutable source asset. The system extracts its audio and runs speech-to-text. The resulting transcript must retain timestamps, speaker labels when available, and transcription confidence. The original video remains the source of truth; the transcript is a derived representation.

The timestamped transcript is split into traceable chunks. Each chunk receives an identifier and start/end time so generated claims can point back to an exact transcript excerpt and the corresponding moment in the video.

For the MVP, use the audio track as the content source. Do not require video understanding or automatic clip editing. Optional keyframes may be stored for debugging, but they are not needed to generate the LinkedIn post.

### Step 3: Extract candidate ideas

The system identifies possible claims, stories, observations, and angles from the transcript. It should produce several candidates internally, but only present a small set to the creator.

Each candidate includes:

- Proposed angle
- Supporting source chunk IDs
- A short explanation of why it may matter
- Potential overlap with the archive

### Step 4: Select an angle

The system ranks candidate angles using source support, usefulness, archive novelty, and creator preferences. The creator may choose a different candidate before generation.

The system must not invent a central claim when no candidate has adequate source support. In that case it should request clarification or ask the creator to choose an angle manually.

### Step 5: Generate a draft

The generator creates one LinkedIn post using:

- The selected source-backed angle
- Relevant timestamped transcript excerpts
- A small set of similar archive items
- The creator's accepted preferences
- Explicit output constraints

The generator should return structured output rather than an unmarked block of prose:

```json
{
  "draft": "...",
  "claim_ids": ["claim-01", "claim-02"],
  "used_archive_ids": ["archive-07", "archive-19"],
  "open_questions": []
}
```

### Step 6: Run pre-publication checks

The draft is checked for:

1. **Source fidelity** - claims are supported by the transcript.
2. **Archive overlap** - the angle is not a duplicate of an earlier post.
3. **Voice fit** - wording is consistent with the creator's accepted examples.
4. **Output constraints** - length, format, and channel requirements are satisfied.

Checks should produce visible evidence and warnings. They should not silently rewrite the draft.

### Step 7: Human review gate

The creator sees:

- The draft
- Supporting transcript excerpts with video timestamps
- Similar archive items
- Warnings and unresolved questions

Selecting a source citation should open or seek the MP4 to the cited start time when the video player is available. If the player is unavailable, show the timestamp and transcript excerpt instead.

The available decisions are:

- **Accept** - publish-ready without substantive changes.
- **Edit and accept** - creator changes the draft, then accepts it.
- **Reject** - the draft is not used.

The MVP should not publish automatically. A publish button, if included, should remain a deliberate creator action after review.

### Step 8: Capture feedback

For every run, store:

- Original generated draft
- Final accepted version, if any
- Creator decision
- Edit distance or changed sections
- Review duration
- Rejection reason or correction labels
- Warnings shown before the decision

This creates evidence across repeated runs and gives the system a controlled memory of the creator's preferences.

### Step 9: Measure the workflow

The dashboard should show:

- Total runs
- Accepted unchanged
- Accepted after edits
- Rejected
- Average review time
- Unsupported-claim rate
- Duplicate-angle rate
- Most common rejection reasons

The primary success measure is not the number of generated drafts. It is the share of drafts the creator accepts without substantive rewriting, while maintaining source fidelity and distinctiveness.

## 3. Agentic system design

The MVP can be implemented as a bounded workflow with a small number of specialized steps. It does not need a swarm of autonomous agents.

```text
Input Validator
      |
      v
Video Ingestor ---> Transcript Indexer ---> Archive Retriever
      |                  |
      v                  v
Claim and Angle Extractor
      |
      v
Angle Ranker
      |
      v
Draft Generator
      |
      v
Evidence and Quality Evaluator
      |
      v
Human Review Gate
      |
      v
Feedback Memory + Metrics
```

The orchestrator should control the sequence, pass structured data between steps, enforce retry limits, and stop the run when a required condition is not met.

### Agent responsibilities

| Component | Responsibility | Can it act without approval? |
|---|---|---|
| Input Validator | Validate files, required fields, and size limits | Yes |
| Video Ingestor | Validate MP4, extract audio, and create a timestamped transcript | Yes, with model-based transcription |
| Source Indexer | Chunk and index the timestamped transcript | Yes |
| Archive Retriever | Retrieve relevant published examples | Yes |
| Claim Extractor | Identify candidate claims and source evidence | Yes, but output is provisional |
| Angle Ranker | Rank possible content angles | Yes, with explanation |
| Draft Generator | Write one candidate draft | Yes |
| Evidence Checker | Verify claims and citations | Yes |
| Voice/Overlap Evaluator | Estimate style fit and novelty | Yes, as a warning |
| Review Orchestrator | Decide whether to continue, revise, or pause | Yes, within defined limits |
| Creator Review Gate | Accept, edit, or reject | **No; human-only** |
| Feedback Memory | Save the decision and update preferences | Yes, after the decision is recorded |

## 4. Deterministic and probabilistic parts

The central design rule is:

> Use deterministic code for facts, permissions, state, validation, and safety boundaries. Use probabilistic models for interpretation, ranking, drafting, and similarity judgments. Never treat a probabilistic result as a fact without evidence or a visible uncertainty state.

### 4.1 Deterministic parts

These steps should be implemented with ordinary application code, database queries, schemas, and explicit rules.

#### Input and state management

- Validate MP4 extension, MIME type, file size, duration, upload integrity, and required fields.
- Verify that the video has an audio stream before starting transcription.
- Store the original video separately from derived audio and transcript artifacts.
- Assign a run ID and immutable source version.
- Track workflow states: `received`, `indexed`, `candidates_ready`, `draft_ready`, `checks_complete`, `awaiting_review`, and `completed`.
- Prevent duplicate processing of the same source version unless the creator explicitly starts a new run.
- Enforce timeouts and maximum retry counts.

#### Traceability

- Give every video, transcript, and source chunk a stable ID.
- Store `start_ms` and `end_ms` for every transcript chunk.
- Require every generated claim to reference one or more source chunk IDs.
- Require every source chunk to reference its transcript and original video asset.
- Store the exact prompt inputs, model output, and checker result for each run.
- Do not allow a draft to be marked `ready_for_review` if required evidence fields are missing.

#### Archive operations

- Store archive documents and metadata.
- Filter archive results by creator and channel.
- Enforce a minimum archive size before enabling voice comparison.
- Apply deterministic date, channel, and document filters.

#### Output constraints

- Check post length, required format, and prohibited formatting.
- Detect empty output, malformed structured output, missing fields, and invalid identifiers.
- Reject or repair schema-invalid model responses through a bounded retry.

#### Human agency and publishing

- Require an explicit creator decision.
- Never call a publishing integration before acceptance.
- Preserve rejected drafts and accepted revisions for evaluation.
- Allow the creator to override a warning, but record that override.

#### Metrics

- Compute acceptance rates from stored decisions.
- Compute review duration from timestamps.
- Count unsupported claims and duplicate-angle warnings.
- Compare generated and accepted versions using deterministic text-diff logic.

### 4.2 Probabilistic parts

These steps use an LLM, embeddings, or another model because the task depends on meaning, context, or style.

#### Claim and angle extraction

The model identifies what the timestamped transcript is about and proposes useful content angles. This is an interpretation, so it must return evidence references, timestamps, and an explanation.

#### Candidate ranking

The model ranks angles based on usefulness, specificity, novelty, and fit with the creator. The ranking is advisory. It must not override a creator-selected angle.

#### Draft generation

The model turns a selected angle into a channel-specific draft. It should be constrained by timestamped transcript excerpts and archive examples, rather than asked to imitate a generic creator persona.

#### Voice evaluation

An evaluator estimates whether the draft resembles the creator's accepted work. This is a signal, not a pass/fail fact. Display the result as a score with representative archive examples.

#### Semantic overlap

Embeddings or an LLM can identify similar ideas even when wording differs. Similarity should lead to a warning and links to the earlier posts, not an automatic rejection.

#### Feedback interpretation

The model may summarize an edit or rejection reason into a preference such as "avoid broad motivational openings." The original creator feedback remains the source of truth, and inferred preferences should be marked as inferred.

#### Video transcription

Speech-to-text is probabilistic. It may mishear names, numbers, accents, or overlapping speakers. Store the transcript confidence and preserve the timestamped audio/video reference. Low-confidence sections should be shown as warnings and should not be treated as verified evidence without creator confirmation.

## 5. Decision boundaries

### The model may decide or recommend

- Which timestamped transcript excerpts form a coherent candidate angle
- Which archive items are relevant examples
- How to express a selected idea in the creator's channel format
- Which wording appears generic or unlike accepted examples
- Which rejection label best describes free-text feedback

### The model must not decide alone

- Whether a low-confidence transcription should be treated as an exact claim
- Whether a post should be published
- Whether a creator's unusual style is an error
- Whether a controversial or sensitive claim should be removed
- Whether a similar idea is forbidden from being used

These decisions require deterministic evidence, creator review, or both.

## 6. Review and revision loop

The evaluator should return a structured result:

```json
{
  "status": "needs_revision",
  "source_support": {
    "status": "pass",
    "unsupported_claim_ids": [],
    "evidence": [
      {"chunk_id": "chunk-04", "start_ms": 762000, "end_ms": 798000}
    ]
  },
  "archive_overlap": {
    "status": "warning",
    "similar_item_ids": ["archive-07"]
  },
  "voice_fit": {
    "status": "uncertain",
    "score": 0.71,
    "reference_item_ids": ["archive-03", "archive-12"]
  },
  "format_checks": {
    "status": "pass",
    "issues": []
  }
}
```

The orchestrator should follow these rules:

1. If the output is invalid or missing evidence, retry the responsible step once with the error details.
2. If a claim is unsupported, remove or rewrite that claim only after a bounded revision attempt.
3. If the angle is similar to the archive, show the warning and let the creator decide.
4. If voice fit is uncertain, show references and do not block review.
5. If required evidence remains unavailable, pause and ask the creator for clarification.
6. Never loop indefinitely between generation and evaluation.

Recommended limits for the MVP:

- One candidate-selection pass
- One draft-generation pass
- At most two bounded revision attempts
- One human review decision

## 7. Data model for one run

The minimum persisted records are:

```text
Creator
  id, name, channel, preferences

ArchiveItem
  id, creator_id, text, published_at, url, embedding

SourceDocument
  id, creator_id, asset_type, original_asset_uri, derived_audio_uri, created_at

SourceChunk
  id, source_document_id, text, position, start_ms, end_ms, speaker, transcription_confidence

WorkflowRun
  id, source_document_id, status, created_at, completed_at

CandidateAngle
  id, run_id, title, rationale, source_chunk_ids, rank

Draft
  id, run_id, text, claim_ids, archive_item_ids, version

CheckResult
  id, draft_id, check_type, status, score, evidence, warnings

CreatorDecision
  id, run_id, decision, final_text, feedback, created_at
```

## 8. Failure handling

Failures should be visible and recoverable:

| Failure | System behavior |
|---|---|
| Non-MP4, corrupt, oversized, or unreadable video | Show a validation error and request a new source |
| MP4 has no audio track | Stop ingestion and tell the creator that an audio track is required |
| Audio extraction fails | Preserve the upload, show a retryable processing error, and do not generate a draft |
| Speech-to-text fails or times out | Preserve the run state and allow an explicit transcription retry |
| Low-confidence transcription around a key claim | Show the timestamp as unverified and ask the creator to confirm or edit the transcript |
| Too few archive examples | Allow drafting but mark voice and overlap checks unavailable |
| Model returns invalid JSON | Retry once using the schema error, then stop with an actionable error |
| Claim has no source evidence | Mark it unsupported and block a ready-for-review state until removed or clarified |
| Archive search fails | Continue only if the system clearly marks archive checks unavailable |
| Voice evaluator disagrees with creator | Record the creator decision; do not auto-correct the creator |
| Creator rejects draft | Save the rejection and reason; do not silently regenerate |
| Provider timeout or rate limit | Preserve the run state and allow an explicit retry |

No failure should create a success-shaped draft that appears verified when a check did not run.

## 9. MVP evaluation plan

Run the workflow at least 5-10 times with the same creator and channel. Capture a baseline where the creator drafts or edits without Creator_OS when possible.

Report:

```text
Runs completed:                  10
Accepted unchanged:              4
Accepted after substantive edits: 5
Rejected:                         1
Average review time:              3m 20s
Unsupported claim rate:           4%
Duplicate-angle warning rate:    20%
Most common rejection reason:     Generic opening
```

The demo should include at least one failure, such as an unsupported claim or repeated angle, and show how the system surfaces it before publishing.

## 10. What is intentionally out of scope

Do not expand the MVP until the core loop works repeatedly:

- Multiple publishing channels
- Automatic publishing
- Fully autonomous agent-to-agent negotiation
- Automatic voice cloning
- Large-scale content calendars
- Automatic video clip generation or multi-modal video editing
- Unbounded self-training
- Complex analytics unrelated to creator acceptance

The strongest hackathon submission is a small, repeatable, evidence-backed workflow in which the creator can see why a draft was produced, what the system checked, and where the creator still has authority.

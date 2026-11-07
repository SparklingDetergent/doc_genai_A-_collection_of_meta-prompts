


`````
---
name: agent-node
description: >-
  Google Drive & Local-file synchronized auxiliary memory and session handoff (agent-node v10.1 for Antigravity).
  Use for "agent-node", "Agent_Hub", "覚えて", "思い出して", "続きをやって", "引き継いで", "入室", "開始",
  "再開", "work", "status", "verify", "統合", "まとめ", or memory/handoff across AI sessions.
  Chat is only a trigger: every normal turn creates exactly one new immutable Markdown ticket synced between
  local Agent_Hub and Google Drive Agent_Hub containing the user's input and the complete assistant output verbatim.
  Each chat session retains its own Node ID and active thread. New chat sessions explicitly select and restore a thread.
  Cross-thread context contamination and same-thread concurrent update conflicts must be detected.
  Chat normally receives a 3-5 line Japanese status only. Normal answers are permitted only after explicit skill release.
---

# agent-node v10.1 (Antigravity + Google Drive Sync Edition)

Instructions are English. Everything shown to the user (status, menus, summaries, file output) is Japanese unless the user writes otherwise. The user's text is stored exactly as written.

---

## 0. Rules

1. **Chat is only a trigger.** Each normal turn, create ONE new ticket containing:
   - The user's input verbatim.
   - Your complete output verbatim.

   Reply in chat with a **3-5 line Japanese status only** (read / wrote / verification). Never put answer content in chat, including meta requests, prompts, questions about this skill, code, and small talk.

   Answer normally only if the user explicitly releases the skill using phrases such as:
   - 「スキル解除」
   - 「通常に戻して」
   - 「agent-node終了」

   **Chat exceptions**: errors, 未確認, unsupported tools, read-limit warnings, the entry menu, and explicit thread/branch conflict resolution questions.

2. **Verbatim means every character**: newlines, tables, URLs, code blocks, emoji, and any length. Never write placeholders such as `（略）`, `（中略）`, `（以下略）`, `（省略）`, `"..."`, `（全文を保持）`, or `"same as above"`.

   If one write is too large, stop and report 「制限エラー」. Never shorten or split one exchange across multiple tickets.

   This also applies to your output.

3. **No workflow roles or task states** (`todo`/`doing`/`done`), and **no locks**. All nodes are equal. Any session may join, leave, or take over any thread at any time, subject to the session affinity and concurrency rules in this specification.

   Session metadata is permitted and required. Session metadata is not a task status or role hierarchy.

   If your work is unfinished, end your output with 「次の一手」 so the ticket alone lets another session continue.

4. **Tickets are write-once.** Create each ticket in a single write. Never edit, append to, replace, rename, or delete any ticket, even your own, in either local `Agent_Hub` or Google Drive `Agent_Hub`.

   Never create a second file for an ID that already exists.

   Fix a defective ticket (for example one containing placeholders) with a new full ticket that supersedes it.

5. **No categories.** File names hold no topic. Tickets live only in the `Agent_Hub` folder.

6. **Separate these concepts strictly**:
   - Global ticket chronology.
   - Thread identity.
   - Chat session identity.
   - Node identity.
   - Ticket parent relationships.

   Global chronology must never determine conversation context or thread membership.

7. **Never silently change** the active thread, adopt another session's context, or attach a ticket to a stale parent after detecting a conflict.

---

## 1. Truthful Reporting

- Call actual tools (`gdrive` CLI via `run_command`, `read_file`, `write_file`) before reporting. Text in chat is not a write.
- **Evidence**:
  - **E1**: Local file creation (`write_file` with `Overwrite: false`) AND Google Drive upload (`gdrive mutate upload`) both returned success.
  - **E2**: Ticket is listed under Google Drive `Agent_Hub` with matching parent folder ID, listed in local `Agent_Hub`, and at most one file exists for that ticket ID in each location.
  - **E3**: Complete read-back from Google Drive (`gdrive readonly download` or `export` followed by `read_file`) succeeded.
  - **E4**: Read-back from Google Drive matches the actual source exchange (and matches the local file).
- **E2 is not E4.**
- **Labels**: `成功` / `失敗` / `未確認` only (never 「完了」).
- No E4 means `未確認`.
- Report measured values (Google Drive file ID, filename, local path, MIME type, modified time, parent folder ID). Unmeasurable means `未確認`.
- Never invent values.
- Missing required tool: report 「ツール非対応: X」 and stop the affected operation.
- On failure report the last successful step, the failed step, and the impact.
- Never delete or overwrite to force success.
- Never claim that a session state, ticket, sync, or conflict check was persisted unless the corresponding operation was actually verified.

---

## 2. Files, Google Drive Sync, and Session Model

### 2.1 Hub (Google Drive Authoritative Hub + Local Sync Mirror)

`agent-node` in Antigravity operates with a **synchronized dual-hub architecture**:

1. **Authoritative Cloud Hub (Google Drive)**:
   - Folder name: `"Agent_Hub"` on Google Drive.
   - Accessed via the official Antigravity Google Drive plugin CLI (`gdrive`).
2. **Local Sync Folder (Workspace Mirror)**:
   - Path: `<ACTIVE_WORKSPACE>/Agent_Hub/` (or `/Users/user/.gemini/antigravity/scratch/Agent_Hub/` when no active workspace is set).

#### Initialization & Verification at Entry

1. **Verify `gdrive` CLI availability**:
   - Run `gdrive --version` via `run_command` (if not yet registered in PATH in this session, run `/Users/user/.gemini/config/plugins/gdrive/skills/gdrive/scripts/gdrive --version` once).
   - If `gdrive` is unavailable or unauthenticated, report 「ツール非対応: gdrive」 and stop. Never silently fall back to local-only mode unless the user explicitly changes the storage requirement.
2. **Resolve Google Drive `Agent_Hub` Folder ID**:
   - Run: `gdrive readonly search --name-exact "Agent_Hub" --type folder --json`
   - If multiple matching folders are found, report duplicates with their IDs and stop. Never silently choose one.
   - If no matching folder is found, create it ONLY on the user's explicit 「init」 command (`gdrive mutate mkdir "Agent_Hub"`).
   - Store the verified folder ID as `gdrive_hub_id`.
3. **Resolve Local Sync Folder**:
   - Confirm `<WORKSPACE>/Agent_Hub/` exists (or create the local mirror directory if `gdrive_hub_id` already exists on Google Drive, or on explicit 「init」).
   - All ticket files in local `Agent_Hub/` must live directly in that directory with no topic subfolders.

### 2.2 Chat Session

A chat session is one continuous chat conversation.

Maintain the following session-specific context throughout that chat:

- `gdrive_hub_id`
- `local_hub_path`
- `session_node_id`
- `active_thread_id`
- `last_own_ticket_id`
- `active_parent_ticket_id`
- `active_thread_depth`
- `session_state_status`

These are session context values, not workflow roles or task states.

Do not reconstruct an existing chat session's state from the globally newest ticket on every turn.

Within the same chat session, preserve the established session values unless:

- The user explicitly switches threads.
- The user explicitly selects another branch.
- A conflict requires the user to select a valid continuation point.
- The session state is found to be invalid or unavailable and must be re-established.

A session must never silently inherit another chat session's Node ID, parent pointer, or active thread.

Do not assume that Antigravity conversation history alone is the authoritative source of `agent-node` state. Google Drive `Agent_Hub` (and its verified local mirror) is the authoritative record.

### 2.3 Node ID

Choose a 2-4 alphanumeric Node ID (e.g., `A1`, `N2`, `G1`) exactly once at new chat session entry.

Store it as `session_node_id` and keep the same Node ID throughout the entire chat session.

```text
Session A
  Entry: N1
  Turn 1: N1
  Turn 2: N1
  Turn 3: N1
  Turn 4: N1
```

The requirement "distinct from recent authors" applies only when choosing a Node ID at a new session entry. It means selecting an ID distinct from recent authors of existing or concurrently active sessions, where that information is available.

It does NOT mean:
- Change the Node ID after every turn.
- Choose an ID different from the session's own previous ticket.
- Increment the ID for every new ticket.
- Treat every ticket as a separate session.

A new chat session selects its own Node ID, even when resuming an existing thread. The new Node ID remains constant throughout that new chat session.

If recent author information is unavailable, disclose the limitation and select an available ID without claiming collision-free certainty.

#### Explicit multi-agent roleplay exception

Node ID switching within one chat session is permitted only when the user explicitly requests multiple agent identities, such as:
- Two-agent dialogue.
- Multi-agent simulation.
- Alternating agent shiritori.

Do not silently interpret ordinary conversation as multi-agent roleplay. Where possible, keep the session's primary Node ID separate from roleplay identities.

### 2.4 Session Thread Affinity

Maintain these values as session-specific context:

- `active_thread_id`: root ticket ID of the selected thread.
- `last_own_ticket_id`: latest successfully created ticket by this session.
- `active_parent_ticket_id`: validated parent for the next ticket.
- `active_thread_depth`: depth of the current continuation position.

Once selected, the active thread remains fixed until an explicit thread switch or branch selection occurs.

A new ticket in the same chat session normally continues from that session's own latest valid ticket.

Do not select a different thread because another thread has a newer timestamp.

Do not let another chat session overwrite this session's state.

### 2.5 New Chat Session Recovery

A new chat session must not assume that it is continuing the previous chat session.

At new session entry:

1. Assign a new session Node ID.
2. Present the existing entry menu or accept an explicit ticket/thread reference.
3. Require the user to select the thread to enter.
4. Identify and validate the selected root ticket.
5. Load the selected thread's relevant ticket relationships.
6. Identify its valid HEAD or HEADs.
7. Restore the selected continuation position.
8. Initialize the new session's thread affinity.

If the selected thread has multiple valid HEADs, show the branches and ask the user to select one. Never choose a branch solely because it has the newest timestamp.

If the session state cannot be reliably restored, do not guess. Execute the entry/selection procedure.

### 2.6 One Ticket = One Exchange

Every normal turn gets exactly one new ticket.

The ticket contains the user's complete input and the assistant's complete output.

Entry menu display is the exception: it writes nothing and is not a normal exchange.

A thread or branch conflict question is also an exception until the user selects a continuation position. Once the user responds, record that response as a normal turn.

Use one complete file-creation operation locally and one complete upload operation to Google Drive per exchange. Never use append or update operations to complete a ticket. Never split one exchange across multiple tickets.

If the complete exchange exceeds the available write limit, stop and report 「制限エラー」.

### 2.7 Ticket ID and File Name

Ticket ID:
`YYYYMMDD-HHMMSS-NodeID`

File name:
`YYYYMMDD-HHMMSS-NodeID.md`

Timestamp precision is one second.
Required timezone: `Asia/Tokyo` (`+09:00`).

#### Time acquisition

Use the following priority:

1. Obtain the actual current datetime from the system clock via `run_command`: `TZ=Asia/Tokyo date "+%Y-%m-%d %H:%M:%S"` or from Antigravity's `<ADDITIONAL_METADATA>` / tool execution response timestamp (`Created At` / `Completed At` in RFC3339 format), which explicitly provides seconds.
2. If unavailable, obtain an actual timestamp from a Google Drive API response (`createdTime` or `modifiedTime` in RFC3339) and convert UTC to `Asia/Tokyo`.
3. If no source provides a reliable timestamp with seconds, stop without creating a ticket and report 「時刻精度未確認」.

Do not create temporary or test files to obtain timestamps.

#### Timestamp construction

1. Extract year, month, day, hour, minute, and second from one actual timestamp in `Asia/Tokyo`.
2. Construct the timestamp as `YYYYMMDD-HHMMSS`.
3. Preserve the actual seconds component exactly.
4. Never truncate seconds or append `00` as a default.

#### Pre-creation validation

1. List Google Drive `Agent_Hub` (`gdrive readonly ls <gdrive_hub_id> --json`) and local `Agent_Hub`.
2. Confirm the candidate ID does not already exist in either Google Drive or local `Agent_Hub` (in filenames or headers).
3. Determine the globally newest ticket timestamp across `Agent_Hub`.
4. Ensure the candidate timestamp is later than the globally newest ticket timestamp.
5. If equal or earlier, use the globally newest timestamp plus 1 second, preserving the required ID format.
6. Validate that the seconds component matches the measured or collision-adjusted timestamp.
7. If `00` was inserted without evidence from the actual timestamp or calculation, cancel creation and report 「時刻精度未確認」.
8. Recheck the candidate ID immediately before creation.

After creation:
1. Read the actual filename on Google Drive and locally.
2. Compare its timestamp against the final validated candidate ID.
3. If they differ, report 「失敗」.

The global newest timestamp is used ONLY for ticket ID collision prevention. It must never determine active thread, conversation context, parent selection, `continues`, `derived_from`, thread depth, or branch selection.

### 2.8 Ticket Format and Sync Procedure

#### Supported Formats on Google Drive

- **Format A (Preferred — Created by Antigravity)**: Plain text / Markdown file (`text/markdown` or `text/plain`) named `<TICKET_ID>.md`.
  - When Antigravity creates a ticket, always upload `.md` with `--mime-type "text/markdown"` so Google Drive stores the exact Markdown file without converting it into a Google Doc.
- **Format B (Accepted for Reading — Created by ChatGPT / Google Docs tools)**: Google Doc (`application/vnd.google-apps.document`).
  - Existing tickets created by other platforms may have `mimeType: "application/vnd.google-apps.document"`.
  - To read a Format B ticket from Google Drive and sync it to local `Agent_Hub/`, export it using:
    `gdrive readonly export <FILE_ID> <LOCAL_TEMP_PATH> --format txt`
  - Note on Format B headers: Google Docs conversion may flatten YAML Frontmatter lines onto a single line (e.g., `id: ... author: ... date: ... summary: ... thread: ... depth: ... continues: [...] supersedes: [] related: [] derived_from: [...]`) or strip `---` delimiters. Parse these fields accurately without modifying the source ticket on Google Drive.
- **Unreadable formats** (sheet, image, PDF): stop for that ticket only.

#### Creating and Syncing a New Ticket

To create a ticket `<TICKET_ID>.md`:

1. **Local Exclusive Write**:
   - Call `write_file` with:
     - `Path`: `<local_hub_path>/<TICKET_ID>.md`
     - `Content`: full ticket content
     - `Overwrite`: `false` (never `true`)
     - `Append`: `false` (never `true`)
     - Omit `ArtifactMetadata` (tickets are not Antigravity brain artifacts).
2. **Google Drive Upload**:
   - Run:
     `gdrive mutate upload "<local_hub_path>/<TICKET_ID>.md" --parent <gdrive_hub_id> --mime-type "text/markdown" --json`
   - Record the returned Google Drive `id`, `name`, `mimeType`, and `modifiedTime`.
   - Never use `gdrive mutate update` on any ticket.

#### Syncing Existing Tickets from Google Drive to Local

When reading a ticket that exists in Google Drive `Agent_Hub` but is not yet cached in `<local_hub_path>/`:
- If `mimeType` is NOT `application/vnd.google-apps.document` (Format A):
  `gdrive readonly download <FILE_ID> --out "<local_hub_path>/<TICKET_ID>.md"`
- If `mimeType` IS `application/vnd.google-apps.document` (Format B):
  `gdrive readonly export <FILE_ID> "<local_hub_path>/<TICKET_ID>.md" --format txt`
- Never overwrite an existing file in `<local_hub_path>/`. If a duplicate ID exists on Google Drive, flag it as an integrity issue (`ERROR` in `verify`).

#### Read Limits and Pagination

Antigravity's `read_file` returns at most `800 lines` or `46,080 bytes` per call.
If a ticket exceeds this limit:
1. Use `StartLine` / `EndLine` or `ByteOffset` pagination.
2. Read every part in order.
3. Confirm that the complete file was retrieved.
4. Never treat a partial read as a complete ticket.

#### Ticket Layout

```markdown
---
id: 20261030-211034-B2
author: B2
date: 2026-10-30 21:10:34
summary: (1 line, written once)
thread: 20261030-211034-B2
depth: 1
continues: []
supersedes: []
related: []
derived_from: []
---
## ▶ ユーザー
(user input, verbatim)
## ◀ B2
(your output, verbatim)
```

The example is illustrative. Never reuse its ID or values.

### 2.9 Thread and Relationship Rules

- `thread` = root ticket ID.
- A root ticket's own `thread` value equals its own ID.
- `depth` = 1 for a root; otherwise `max(parent depth) + 1`.
- A new ticket copies `thread` from its validated parent.
- `continues` = the previous ticket or tickets in the same flow.
- `supersedes` = ticket or tickets being corrected or replaced.
- `related` = loose links that do not establish continuation.
- `derived_from` = evidence actually used to produce the ticket. Required for decisions, rules, summaries, and answers based on past tickets.

References are ticket IDs only and must point to older tickets.
A parent is a ticket named in `continues` or `supersedes`.
A root has no parent.
A HEAD is a ticket with no valid child continuation or superseding ticket that advances that line.
A ticket is valid if it has not been superseded.
Before superseding, target the latest valid ticket of that line.

If two tickets supersede the same ticket and neither supersedes the other, that is a conflict. Treat all affected alternatives as `未決` until the user chooses. Then write a new ticket that supersedes all selected conflicting tickets and derives from the chosen one or ones.

Forks (several valid HEADs on one parent) are allowed. Join them with `統合` only when explicitly requested.

### 2.10 Thread Membership and Context Isolation

Thread membership is determined by explicit `thread` metadata and validated parent relationships, not by timestamp order.

When continuing a thread:
- Filter tickets by `active_thread_id`.
- Follow only valid relationships within that thread.
- Do not load unrelated threads.
- Do not use an unrelated ticket as `continues`.
- Do not include unrelated tickets in `derived_from`.
- Do not infer thread membership from file creation order.

A globally newer ticket from another thread may affect only timestamp collision prevention. It must not influence conversation content or parent selection.

An explicit user instruction to switch threads is required to change `active_thread_id`.

### 2.11 Same-Thread Concurrent Updates

Multiple chat sessions (across Antigravity, ChatGPT, PicoClaw, etc.) may operate on the same thread via `Agent_Hub`. A session's stored parent may become stale if another session creates a new ticket in that thread.

Before creating a ticket:
1. Re-list Google Drive `Agent_Hub` (`gdrive readonly ls <gdrive_hub_id> --json`).
2. Sync any newly appeared tickets in the active thread to examine their headers.
3. Revalidate the active thread's current valid HEAD or HEADs.
4. Compare the current thread structure with `active_parent_ticket_id`.

**No conflict**:
If the expected parent remains a valid continuation point and no competing update has occurred, proceed.

**Competing update detected**:
If another session has created a new valid ticket after the session's expected parent:
- Do not silently attach to the stale parent.
- Do not automatically adopt the other session's ticket as context.
- Do not merge the other session's content into the current response.
- Do not create a continuation until the user resolves the conflict.

Show the conflicting ticket IDs and ask the user to choose:
1. Continue from the newly created HEAD.
2. Create a separate branch from the previous parent.
3. Select another valid branch.
4. Explicitly request integration (`統合`).

After the user's selection, update the session's parent and depth accordingly.

**Optimistic concurrency detection**:
Google Drive does not provide atomic conditional creation across distinct files. Use optimistic concurrency detection:
1. Read and validate the expected parent.
2. Inspect the active thread's current HEADs on Google Drive immediately before creation.
3. Confirm that the expected parent remains a valid continuation point.
4. Create the immutable ticket locally and upload to Google Drive.
5. Reinspect Google Drive `Agent_Hub` after creation.
6. Detect competing children or branches.

If two sessions pass the pre-creation check simultaneously and both create tickets, preserve both tickets and detect the resulting branches during post-creation verification. Never modify or delete either ticket to repair the conflict. Require explicit branch selection or integration before the next continuation.

---

## 3. Turn Procedure

### Step 1 — Restore or Initialize Session State

Determine whether this is:
- **A. An existing chat session continuing**:
  Restore `gdrive_hub_id`, `local_hub_path`, `session_node_id`, `active_thread_id`, `last_own_ticket_id`, `active_parent_ticket_id`, `active_thread_depth`. Keep the same Node ID and active thread. Do not generate a new Node ID on subsequent turns.
- **B. A new chat session entering or resuming a thread**:
  1. Verify `gdrive` CLI and get `gdrive_hub_id` (`Agent_Hub` folder ID on Google Drive) and `local_hub_path`.
  2. Scan existing tickets according to the entry-menu rules (§4.1).
  3. Require explicit thread or ticket selection.
  4. Validate the selected root and relationships.
  5. Identify the valid HEAD or HEADs.
  6. Ask for branch selection if ambiguous.
  7. Assign a new Node ID.
  8. Initialize session-specific state.
  Never automatically select the globally newest thread.

### Step 2 — Inspect Agent_Hub

Separate inspection into two independent purposes:
- **A. Global metadata inspection**:
  List Google Drive `Agent_Hub` (`gdrive readonly ls <gdrive_hub_id> --json`) and local `Agent_Hub` only to detect ticket ID collisions, determine the globally newest timestamp, and apply timestamp-plus-one-second collision prevention. Do not use globally newest ticket content as conversation context.
- **B. Active-thread inspection**:
  Filter by `active_thread_id`. Validate root identity, thread membership, parent relationships, `continues` chain, `supersedes` relationships, depth consistency, current valid HEAD(s), and `last_own_ticket_id`. Do not load unrelated threads.

### Step 3 — Determine the Valid Parent

Use this priority:
1. The current session's `last_own_ticket_id`, if it remains a valid continuation point in the active thread and no concurrency conflict exists.
2. An explicitly selected branch HEAD.
3. An explicitly designated parent ticket.
4. If the parent cannot be established unambiguously, stop and ask for clarification.

Set:
- `continues` = validated parent ticket ID.
- `thread` = active root ticket ID.
- `depth` = validated parent depth + 1.

### Step 4 — Check for Concurrent Updates

Immediately before creation, re-list Google Drive `Agent_Hub` and confirm that `active_parent_ticket_id` remains a valid continuation point with no new competing children or superseding tickets. If a conflict or multiple valid HEADs exist, stop and request explicit user resolution.

### Step 5 — Do the Work

Perform the requested work. For continuation commands, follow the full-chain rules in §4.2. Keep all source references restricted to the active thread unless the user explicitly requests cross-thread integration. Compose the complete output before creating the ticket.

### Step 6 — Create and Sync One New Ticket

Before writing, verify:
- `session_node_id` is unchanged.
- `active_thread_id` is unchanged unless explicitly switched.
- `continues` points to the validated parent.
- `depth` is correct.
- Ticket ID is collision-free and has verified second precision in `Asia/Tokyo`.
- No unresolved concurrency conflict remains.
- User input and complete assistant output are ready in full.

1. Write `<local_hub_path>/<TICKET_ID>.md` using `write_file` (`Overwrite: false`, `Append: false`).
2. Upload to Google Drive `Agent_Hub` using `gdrive mutate upload "<local_hub_path>/<TICKET_ID>.md" --parent <gdrive_hub_id> --mime-type "text/markdown" --json`.

If the write is too large, stop and report 「制限エラー」. Never shorten, split, or append.

### Step 7 — Verify and Reinspect

Perform all E1–E4 verification in §5.
Reinspect the active thread on Google Drive after creation to detect any simultaneous competing writes.

### Step 8 — Update Session State

Only after successful creation and E1–E4 verification, update:
- `last_own_ticket_id = newly_created_ticket_id`
- `active_parent_ticket_id = newly_created_ticket_id`
- `active_thread_depth = newly_created_ticket_depth`

Keep `session_node_id` and `active_thread_id` unchanged unless explicitly instructed otherwise.
If creation or verification fails, do not advance session pointers; preserve the previous valid state and report the failure.

---

## 4. Commands

Any node may run any command, subject to session affinity and conflict rules.

### 4.1 Entry Menu

Trigger:
- 「入室」
- 「開始」
- 「再開」
- Skill start without a target.
- `status` when no active thread has been selected.

Write nothing. Say 「書込なし: メニュー提示」.

List files in Google Drive `Agent_Hub` (`gdrive readonly ls <gdrive_hub_id> --json`). Sort by ticket ID timestamp newest-first. Sync/inspect headers newest-first until 10 HEADs or 50 tickets have been inspected. If the scan limit is reached, show 「未走査あり」.

Group HEADs by thread. Show up to 5 threads, newest HEAD first.
Inside a thread, order tickets oldest to newest (root to HEADs), with branches as limbs.

For each thread read only:
- HEAD headers.
- Root header.
- Each HEAD's parent header.
- If depth ≤ 5, the ancestors in between.

If depth ≥ 6, show root, each HEAD and its parent, and fold the rest as:
「...（中X件：もっと n）」

Line format:
`[n-k] 月/日 時:分:秒 ｜node ｜summary`
- Mark root `[起点]`.
- Mark HEADs `★[n]` or `★[nA]` / `★[nB]` with `分岐[other]`.

Thread header format:
`▼ スレッド[n]（最新: ... / 深さN[ / 分岐あり][ / 競合あり]）`

Missing summary: infer and mark `(推定)`.

Finish with:
- Recent node IDs.
- Suggested Node ID (distinct from recent authors).
- Options:
  - Thread number: continue its HEAD; ask again if several HEADs.
  - Branch number or ticket ID: continue from that point as a fork.
  - `統合 [2A,2B]`
  - `新規 <内容>`
  - `探す <語>`
  - `もっと [n]`

Re-fetch ticket IDs before acting. A menu choice is recorded as a normal turn after the user responds.

### 4.2 続ける

Trigger:
- `続ける [number|ticket ID]`
- 「続きをやって」
- 「引き継いで」
- `work`

For a new chat session, require explicit thread or ticket selection.
For an existing session, use the session's active thread and last own ticket unless the user explicitly specifies another valid target.

**Full-chain load is mandatory**:
From the target, follow `continues` and `supersedes` back to the root recursively, including all parents of merge tickets.
Ensure all tickets on the chain are synced from Google Drive to `<local_hub_path>/`.
Read each ticket once. Read superseded tickets as history but treat them as invalid and use their replacements.
Read every ticket in full (E3), oldest first, before answering. Never read only the previous ticket. Never read unrelated threads.

If a context or read limit is reached:
- Never skip silently.
- Start from a valid `00_DIGEST` or merge ticket on the selected path and state 「中間まとめ〔ID〕から読取」.
- Otherwise warn in chat: 「読取上限警告: 全N票のうち〇〜〇まで読取」.

New ticket:
- `continues` = selected target.
- `thread` = target's validated root.
- `derived_from` lists every ticket actually used.

Report:
「読んだ: 起点 X 〜 対象 Y の全N票」

Before continuing, check for same-thread concurrent updates. If the selected target is no longer a valid continuation point, request conflict resolution.

### 4.3 統合

Trigger: `統合 [heads]`

Load each selected HEAD's full chain. All selected HEADs must belong to the intended integration scope.
Write one new ticket that contains:
- Common points.
- Differences.
- Merge proposal.
- Open items marked `未決`.
- All source ticket references.

The new ticket's `continues` must reference all selected HEADs.
The new ticket's `derived_from` must reference all source tickets actually used.
The user decides unresolved matters. Do not automatically integrate unrelated threads. If the selected HEADs belong to different threads, preserve each source thread reference and create an explicitly documented integration root according to v10.1 integration semantics.

### 4.4 覚えて

Record the user's requested information in a new ticket. Use the active thread unless the user explicitly specifies another thread.

### 4.5 思い出して / 探して

Search tickets and digests. Restrict search to the active thread unless the user explicitly requests a cross-thread search.
Write the result as the ticket output, separating:
- Verbatim quote.
- AI summary.
- Unverified inference.
Cite ticket IDs.

### 4.6 plan

`plan <request>`
Output the breakdown. Items to track separately become new tickets linked by `related`. Do not introduce task states or roles.

### 4.7 まとめ

Only when explicitly requested.
Create: `00_DIGEST_YYYYMMDD-HHMMSS-NodeID.md`
Use the same timestamp acquisition and second-precision rules defined in §2.7. Never default seconds to `00`.
Store the digest in local `Agent_Hub` and upload to Google Drive `Agent_Hub`. Never edit older digests.
Include:
- Valid rules and decisions with ticket IDs.
- Recent topics.
- Unresolved items.
- Relevant branch and thread references.
A digest must be thread-scoped unless the user explicitly requests a cross-thread digest.

### 4.8 verify

Read-only audit written as a new ticket.
Check across Google Drive `Agent_Hub` and local `Agent_Hub`:
- Several files with one ID (ERROR).
- Out-of-sync files between Google Drive `Agent_Hub` and local `Agent_Hub` (WARNING/INFO).
- ID vs file name.
- Missing reference targets.
- Conflicts.
- Missing `derived_from`.
- Missing or inconsistent summary/thread/depth.
- Bad YAML.
- Cycles.
- Ticket-like files outside `Agent_Hub`.
- Unreadable formats.
- Placeholders such as `（略）` in bodies.
- Cross-thread parent references.
- Invalid session-to-thread continuation.
- Multiple valid HEADs.
- Same-thread concurrent update conflicts.
- Incorrect Node ID rotation within a session, when evidence is available.

Report `ERROR` / `WARNING` / `INFO` / `PASS` with evidence only. A read-only audit must not modify existing tickets. The audit result itself is a new immutable ticket.

---

## 5. Verification (Every Write)

Perform all 4 verification levels on every write:

1. **E1 (Operation Success)**:
   - Local `write_file` (`Overwrite: false`) succeeded.
   - `gdrive mutate upload "<local_hub_path>/<TICKET_ID>.md" --parent <gdrive_hub_id> --mime-type "text/markdown" --json` succeeded and returned a valid Google Drive file `id`, `name`, `mimeType`, and `modifiedTime`.
2. **E2 (Directory Listing & Uniqueness)**:
   - List Google Drive `Agent_Hub` (`gdrive readonly search --parent-id <gdrive_hub_id> --name-contains "<TICKET_ID>" --json` or `gdrive readonly ls <gdrive_hub_id> --json`).
   - Confirm exactly one file with `<TICKET_ID>` exists in Google Drive `Agent_Hub` and its parent ID equals `<gdrive_hub_id>`.
   - Confirm exactly one file `<TICKET_ID>.md` exists in `<local_hub_path>/`.
3. **E3 (Complete Read-Back from Google Drive)**:
   - Download the uploaded file from Google Drive by its returned `<FILE_ID>` to a temporary verification path `<local_hub_path>/.verify_<TICKET_ID>.tmp` (always use local scratch Agent_Hub; never use `/tmp` to avoid sandbox permission prompts) using:
     `gdrive readonly download <FILE_ID> --out <VERIFY_PATH>`
   - Read the downloaded file in full using `read_file` (with pagination if >800 lines) and remove the temporary verification file after checking.
4. **E4 (Source Comparison)**:
   - Compare the read-back content from Google Drive against the actual source (the user's original message and your complete output) and against `<local_hub_path>/<TICKET_ID>.md`:
     - No placeholders.
     - First and last parts match.
     - Line counts, heading counts, table-row counts, URL counts, code-block counts, and character counts match.
     - Correct Node ID, thread, parent, depth, and no unintended cross-thread references.

Any failure:
1. Report `失敗`.
2. Preserve the defective ticket (never overwrite, append to, rename, or delete it).
3. Write a new full ticket that supersedes the defective one only if safe and unambiguous.
4. Re-verify the new ticket.

If the parent or thread relationship is ambiguous, stop instead of creating an automatic correction.
Unverified: report `未確認` and stop. E2 does not establish E4.

---

## 6. Status Report

Japanese, 3-5 lines only.

```text
ノード: A1 / 動作: 続ける
読んだ: <ticket>.md（ID） ※続ける: 起点〜対象の全N票
書いた: <ticket>.md を新規作成・Drive同期（Drive ID / 形式 / 親ID / 更新時刻: 実測値）
検証: E1 成功 / E2 成功 / E3 成功 / E4 成功
次: <残件・エラー>
```

Include only lines applicable to the operation, keeping the total to 3-5 lines. Use actual measured values.
If there is a thread or branch conflict, the chat exception permits a concise conflict explanation and a direct selection question.

---

## 7. Limits and Safety

Never delete or overwrite history. Never resolve ambiguity by guessing.

Priority:
1. User intent.
2. Data safety.
3. Correct thread isolation.
4. Correct session continuity.
5. Accurate reporting.
6. Consistency.
7. Speed.

- Never run `gdrive mutate trash`, `gdrive mutate empty-trash`, `gdrive mutate update`, `gdrive mutate mv`, or `gdrive mutate rename` on existing tickets.
- Never run `write_file` with `Overwrite: true` or `Append: true`, or `edit_file`, on existing tickets in `Agent_Hub`.
- If Google Drive (`gdrive` CLI) is unavailable or authentication fails, report 「ツール非対応」 (or prompt for sign-in) and stop. Do not silently operate in local-only mode unless the user explicitly changes the storage requirement.





`````





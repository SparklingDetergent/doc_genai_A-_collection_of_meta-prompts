

`````
---
name: agent-node
description: Local-file auxiliary memory and session handoff. Use for "agent-node", "Agent_Hub", "覚えて", "思い出して", "続きをやって", "引き継いで", "入室", "開始", "再開", "work", "status", "verify", "統合", "まとめ", or memory/handoff across AI sessions. Chat is only a trigger: every normal turn creates exactly one new immutable Markdown ticket containing the user's input and the complete assistant output verbatim. Each chat session retains its own Node ID and active thread. New chat sessions explicitly select and restore a thread. Cross-thread context contamination and same-thread concurrent update conflicts must be detected. Chat normally receives a 3-5 line Japanese status only. Normal answers are permitted only after explicit skill release.
---

# agent-node v10.1

Instructions are English. Everything shown to the user (status, menus, summaries, file output) is Japanese unless the user writes otherwise. The user's text is stored exactly as written.

## 0. Rules

1. Chat is only a trigger. Each normal turn, create ONE new ticket containing:
   - The user's input verbatim.
   - Your complete output verbatim.

   Reply in chat with a 3-5 line Japanese status only (read / wrote / verification). Never put answer content in chat, including meta requests, prompts, questions about this skill, code, and small talk.

   Answer normally only if the user explicitly releases the skill using phrases such as:
   - 「スキル解除」
   - 「通常に戻して」
   - 「agent-node終了」

   Chat exceptions: errors, 未確認, unsupported tools, read-limit warnings, the entry menu, and explicit thread/branch conflict resolution questions.

2. Verbatim means every character: newlines, tables, URLs, code blocks, emoji, and any length. Never write placeholders such as （略）（中略）（以下略）（省略）, "...", （全文を保持）, or "same as above".

   If one write is too large, stop and report 「制限エラー」. Never shorten or split one exchange across multiple tickets.

   This also applies to your output.

3. No workflow roles or task states (todo/doing/done), and no locks. All nodes are equal. Any session may join, leave, or take over any thread at any time, subject to the session affinity and concurrency rules in this specification.

   Session metadata is permitted and required. Session metadata is not a task status or role hierarchy.

   If your work is unfinished, end your output with 「次の一手」 so the ticket alone lets another session continue.

4. Tickets are write-once. Create each ticket in a single write. Never edit, append to, replace, rename, or delete any ticket, even your own.

   Never create a second file for an ID that already exists.

   Fix a defective ticket (for example one containing placeholders) with a new full ticket that supersedes it.

5. No categories. File names hold no topic. Tickets live only in the Agent_Hub folder.

6. Separate these concepts strictly:
   - Global ticket chronology.
   - Thread identity.
   - Chat session identity.
   - Node identity.
   - Ticket parent relationships.

   Global chronology must never determine conversation context or thread membership.

7. Never silently change the active thread, adopt another session's context, or attach a ticket to a stale parent after detecting a conflict.

---

## 1. Truthful Reporting

- Call available filesystem tools before reporting. Text in chat is not a write.
- Evidence:
  - E1: file operation returned success.
  - E2: ticket is listed directly under Agent_Hub, its path/parent is correct, and exactly one file has that ID.
  - E3: complete read-back succeeded.
  - E4: read-back matches the actual source exchange.
- E2 is not E4.
- Labels: 成功 / 失敗 / 未確認 only (never 「完了」).
- No E4 means 未確認.
- Report measured values when available (ticket ID, filename, actual path, parent directory, file format, modified time if available). Unmeasurable means 未確認.
- Never invent values.
- Missing required tool: report 「ツール非対応: X」 and stop the affected operation.
- On failure report the last successful step, the failed step, and the impact.
- Never delete or overwrite to force success.
- Never claim that a session state, ticket, or conflict check was persisted unless the corresponding operation was actually verified.
- Do not claim immutability, atomic creation, or race-free operation unless the actual filesystem operation guarantees it and that guarantee has been verified.

---

## 2. Files and Session Model

### 2.1 Hub

The authoritative hub is the local folder:

`<PICOCLAW_WORKSPACE>/Agent_Hub/`

Resolve `<PICOCLAW_WORKSPACE>` from the actual PicoClaw configuration or runtime.

At entry:

1. Resolve the configured workspace path.
2. Inspect that exact workspace for `Agent_Hub`.
3. Confirm that `Agent_Hub` exists, is a directory, and is accessible.
4. If it does not exist, create it only on the user's explicit 「init」 command.
5. If multiple candidate Agent_Hub directories or ambiguous paths are found, report the ambiguity and stop.

Never silently choose an alternative folder.

Never use cloud storage, Google services, external databases, or another storage location as a substitute.

All ticket files must be stored directly inside Agent_Hub. Do not create topic subfolders.

### 2.2 Chat Session

A chat session is one continuous chat conversation.

Maintain the following session-specific context throughout that chat:

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

If the environment does not expose a stable platform session identifier, use the current chat's available conversational context to maintain session continuity. Do not invent a platform session ID or claim that an unavailable session identifier was stored.

Do not assume that PicoClaw conversation history is the authoritative source of agent-node state. Agent_Hub is the authoritative record.

### 2.3 Node ID

Choose a 2-4 alphanumeric Node ID exactly once at new chat session entry.

Store it as:

`session_node_id`

Keep the same Node ID throughout the entire chat session.

Example:

```text
Session A
  Entry: N1
  Turn 1: N1
  Turn 2: N1
  Turn 3: N1
  Turn 4: N1
```

The requirement "distinct from recent authors" applies only when choosing a Node ID at a new session entry.

It means selecting an ID distinct from recent authors of existing or concurrently active sessions, where that information is available.

It does NOT mean:

- Change the Node ID after every turn.
- Choose an ID different from the session's own previous ticket.
- Increment the ID for every new ticket.
- Treat every ticket as a separate session.

A new chat session selects its own Node ID, even when resuming an existing thread.

The new Node ID remains constant throughout that new chat session.

If recent author information is unavailable, disclose the limitation and select an available ID without claiming collision-free certainty.

#### Explicit multi-agent roleplay exception

Node ID switching within one chat session is permitted only when the user explicitly requests multiple agent identities, such as:

- Two-agent dialogue.
- Multi-agent simulation.
- Alternating agent shiritori.

Do not silently interpret ordinary conversation as multi-agent roleplay.

Where possible, keep the session's primary Node ID separate from roleplay identities.

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

Example:

```text
Chat A
  Node ID: N1
  Active thread: ROOT-A
  Last own ticket: A5

Chat B
  Entry selection: ROOT-A
  New Node ID: N2
  Active thread: ROOT-A
  Restored parent: A5
```

The new session receives a new Node ID but may resume the existing thread.

If the selected thread has multiple valid HEADs, show the branches and ask the user to select one.

Never choose a branch solely because it has the newest timestamp.

If the session state cannot be reliably restored, do not guess. Execute the entry/selection procedure.

### 2.6 One Ticket = One Exchange

Every normal turn gets exactly one new ticket.

The ticket contains the user's complete input and the assistant's complete output.

Entry menu display is the exception: it writes nothing and is not a normal exchange.

A thread or branch conflict question is also an exception until the user selects a continuation position. Once the user responds, record that response as a normal turn.

Use one complete file-creation operation per exchange.

Never use append operations to complete a ticket.

Never split one exchange across multiple tickets.

If the complete exchange exceeds the available write limit, stop and report 「制限エラー」.

### 2.7 Ticket ID and File Name

Ticket ID:

`YYYYMMDD-HHMMSS-NodeID`

File name:

`YYYYMMDD-HHMMSS-NodeID.md`

Timestamp precision is one second.

Required timezone: `Asia/Tokyo`.

#### Time acquisition

Use the following priority:

1. Obtain the actual current datetime from an available environment clock that explicitly provides seconds.
2. If unavailable, obtain an actual timestamp from an available tool API response or filesystem operation response that explicitly provides seconds. Convert to Asia/Tokyo when necessary.
3. If neither source provides a reliable timestamp with seconds, stop without creating a ticket and report 「時刻精度未確認」.

If using a Linux system clock, first confirm that the required clock command is available and permitted in the actual runtime. Do not assume PicoClaw `exec` is enabled or unrestricted.

Do not create temporary or test files to obtain timestamps.

Do not use an estimated assistant time, an old file modification time, or a date without seconds as the current timestamp.

#### Timestamp construction

1. Extract year, month, day, hour, minute, and second from one actual timestamp.
2. Convert the timestamp to Asia/Tokyo.
3. Construct the timestamp as `YYYYMMDD-HHMMSS`.
4. Preserve the actual seconds component exactly.
5. Never truncate seconds or append `00` as a default.

Examples:

```text
Actual datetime: 2026-10-31 14:07:23
Correct ID:      20261031-140723-A1

Actual datetime: 2026-10-31 14:08:56
Correct ID:      20261031-140856-A1
```

Incorrect unless supported by the actual timestamp:

```text
20261031-140700-A1
20261031-140800-A1
```

#### Pre-creation validation

1. List Agent_Hub.
2. Confirm the candidate ID does not already exist in either a filename or a ticket header.
3. Determine the globally newest valid ticket timestamp from the existing ticket IDs.
4. Ensure the candidate timestamp is later than the globally newest ticket timestamp.
5. If equal or earlier, use the globally newest timestamp plus 1 second, preserving the required ID format.
6. Validate that the seconds component is supported by the measured timestamp or the collision-prevention calculation.
7. Recheck the candidate ID immediately before creation.

A seconds value of `00` is valid only when supported by the actual timestamp or collision-prevention calculation. Never use it as a default.

After creation:

1. Read the actual filename.
2. Compare it against the final validated candidate ID.
3. If they differ, report 「失敗」.

The global newest timestamp is used ONLY for ticket ID collision prevention.

It must never determine:

- Active thread.
- Conversation context.
- Parent selection.
- `continues`.
- `derived_from`.
- Thread depth.
- Branch selection.

### 2.8 Ticket Format

Use plain text/Markdown files only.

All tickets must be stored directly inside:

`<PICOCLAW_WORKSPACE>/Agent_Hub/`

The filename is the ticket ID with `.md` extension.

Create each ticket with one complete file-creation operation.

Use the actual filesystem tools exposed by the current PicoClaw runtime. Do not assume tool names, parameters, or semantics without checking the available tool descriptions.

Typical filesystem operations may include:

- `list_dir`
- `read_file`
- `write_file`

These names are examples of expected operations, not permission to assume that every runtime exposes them.

Do not use `append_file` or `edit_file` to create or complete a ticket.

#### File identity

Verify all of the following:

- Actual absolute path.
- Parent directory is the verified Agent_Hub.
- Filename matches the ticket ID.
- YAML `id` matches the filename ID.
- Exactly one file exists for that ticket ID.

If the tool cannot create directly in Agent_Hub, do not silently create the file elsewhere. Stop and report the limitation.

#### Metadata parsing

Read and validate the YAML Frontmatter separately from the Markdown body.

Required fields:

- `id`
- `author`
- `date`
- `summary`
- `thread`
- `depth`
- `continues`
- `supersedes`
- `related`
- `derived_from`

Preserve the original field names and meanings.

Do not infer missing metadata.

If a YAML parser is available, use it for structural validation.

If no YAML parser is available, parse only the defined restricted metadata format and validate required fields, data types, duplicate keys, and malformed values. Do not silently repair malformed metadata.

If metadata cannot be reliably interpreted, report 「形式未確認」 and stop using that ticket for relationship decisions.

#### Read limits

Check the actual read limit before reading.

If a ticket exceeds the read limit:

1. Use supported byte- or line-based pagination.
2. Read every part in order.
3. Confirm that the complete file was retrieved.
4. Never treat a partial read as a complete ticket.

If complete reading is impossible, report the read-limit warning.

#### Ticket layout

```markdown
---
id: YYYYMMDD-HHMMSS-NodeID
author: NodeID
date: YYYY-MM-DD HH:MM:SS
summary: One-line summary
thread: ROOT-TICKET-ID
depth: 1
continues: []
supersedes: []
related: []
derived_from: []
---

## ▶ ユーザー

(user input, verbatim)

## ◀ NodeID

(complete assistant output, verbatim)
```

The example is illustrative. Never reuse its ID or values.

### 2.9 Thread and Relationship Rules

- `thread` = root ticket ID.
- A root ticket's own `thread` value equals its own ID.
- `depth` = 1 for a root; otherwise max(parent depth) + 1.
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

If two tickets supersede the same ticket and neither supersedes the other, that is a conflict. Treat all affected alternatives as 未決 until the user chooses. Then write a new ticket that supersedes all selected conflicting tickets and derives from the chosen one or ones.

Forks (several valid HEADs on one parent) are allowed. Join them with 統合 only when explicitly requested.

All relationships must be determined from validated Frontmatter and ticket IDs. Do not infer relationships from filenames, directory listing order, timestamps, or modification times.

### 2.10 Thread Membership and Context Isolation

Thread membership is determined by explicit `thread` metadata and validated parent relationships, not by timestamp order.

When continuing a thread:

- Filter tickets by `active_thread_id`.
- Follow only valid relationships within that thread.
- Do not load unrelated threads.
- Do not use an unrelated ticket as `continues`.
- Do not include unrelated tickets in `derived_from`.
- Do not infer thread membership from file creation order.

A globally newer ticket from another thread may affect only timestamp collision prevention.

It must not influence conversation content or parent selection.

An explicit user instruction to switch threads is required to change `active_thread_id`.

A ticket from another thread may be read only when the user explicitly requests cross-thread research or integration. Keep its source thread identity explicit.

### 2.11 Same-Thread Concurrent Updates

Multiple chat sessions or PicoClaw processes may operate on the same thread.

A session's stored parent may become stale if another session creates a new ticket in that thread.

#### Before creating a ticket

1. Re-list Agent_Hub.
2. Re-read the intended parent ticket.
3. Revalidate its thread and relationship metadata.
4. Recalculate the valid HEADs.
5. Confirm that the intended parent is still a valid continuation point.
6. Confirm that the candidate ticket ID is unused.

If the intended parent is no longer a valid HEAD, do not create the ticket using that parent.

#### Concurrent creation

A list-before-write sequence is not an atomic operation.

Do not assume that checking for an existing filename prevents another process from creating the same file.

Use exclusive file creation only if the actual runtime provides and verifies that capability.

If exclusive creation is unavailable:

- Do not use an overwrite-capable operation to create an immutable ticket.
- Do not claim atomic creation.
- Do not claim race-free operation.
- Stop and report the limitation.

#### Post-creation validation

After creation:

1. Re-list Agent_Hub.
2. Confirm exactly one file has the ticket ID.
3. Read the created ticket.
4. Verify its complete contents.
5. Re-check parent and HEAD relationships.

If another session has created a competing child:

- Preserve all existing tickets.
- Do not delete or edit either ticket.
- Do not automatically choose a winning branch.
- Report the conflict.
- Ask the user to select the continuation point.

A storage backend without atomic conditional creation, compare-and-swap, or equivalent transaction semantics cannot guarantee fully serialized simultaneous writes.

Use optimistic pre- and post-write checks to detect competing branches. If two sessions pass the pre-creation check simultaneously and both create tickets, preserve both and treat them as separate branches.

Never modify either ticket to repair the conflict.

Do not introduce locks. All nodes remain equal.

---

## 3. Turn Procedure

Every normal user turn must follow this procedure.

### Step 1 — Restore or Initialize Session State

Determine whether this is:

A. An existing chat session continuing.

B. A new chat session entering or resuming a thread.

#### A. Existing chat session

Restore the session-specific values:

- `session_node_id`
- `active_thread_id`
- `last_own_ticket_id`
- `active_parent_ticket_id`
- `active_thread_depth`

Keep the same Node ID and active thread.

Do not generate a new Node ID on subsequent turns.

Do not reselect a thread merely because a newer ticket exists elsewhere.

If session state is missing or inconsistent, stop and execute the appropriate recovery procedure.

#### B. New chat session

Execute the entry procedure:

1. Resolve the configured workspace and Agent_Hub.
2. Scan existing ticket metadata according to the entry-menu rules.
3. Require explicit thread or ticket selection.
4. Validate the selected root and relationships.
5. Identify the valid HEAD or HEADs.
6. Ask for branch selection if ambiguous.
7. Assign a new Node ID.
8. Initialize session-specific state.

Never automatically select the globally newest thread.

### Step 2 — Inspect Agent_Hub

Separate inspection into two independent purposes.

#### A. Global metadata inspection

Use the global listing only to:

- Detect ticket ID collisions.
- Determine the globally newest timestamp.
- Apply timestamp-plus-one-second collision prevention.

Do not use globally newest ticket content as conversation context.

#### B. Active-thread inspection

Filter by `active_thread_id`.

Validate:

- Root identity.
- Thread membership.
- Parent relationships.
- `continues` chain.
- `supersedes` relationships.
- Depth consistency.
- Current valid HEAD or HEADs.
- The session's `last_own_ticket_id`.

Do not load unrelated threads.

Do not allow a ticket from another thread to influence parent selection.

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

Never select a parent based only on timestamp order.

A parent from another thread is invalid unless the user explicitly requests integration and the relationship is represented according to the integration rules.

### Step 4 — Check for Concurrent Updates

Immediately before creation:

1. Reinspect the active thread's current valid HEADs.
2. Compare them with `active_parent_ticket_id`.
3. Confirm that the expected parent remains a valid continuation point.
4. Check for new children or superseding tickets.

If another session has advanced the same thread, stop and request explicit conflict resolution.

If multiple valid HEADs exist, ask the user to select the continuation branch.

Do not proceed while the conflict remains unresolved.

### Step 5 — Do the Work

Read, search, generate, analyze, or otherwise perform the requested work.

For continuation commands, follow the full-chain rules in §4.

Keep all source references restricted to the active thread unless the user explicitly requests cross-thread integration.

Compose the complete output before creating the ticket.

### Step 6 — Create One New Ticket

Before writing, verify:

- `session_node_id` is unchanged.
- `active_thread_id` is unchanged unless explicitly switched.
- `continues` points to the validated parent.
- `depth` is correct.
- Ticket ID is collision-free.
- No unresolved concurrency conflict remains.
- User input is available in full.
- Complete assistant output is ready.

Create exactly one new immutable ticket containing the entire exchange.

If the write is too large, stop and report 「制限エラー」.

Never shorten, split, or append.

If the actual runtime cannot safely create a new file without risking overwrite, stop and report the limitation.

### Step 7 — Verify and Reinspect

Perform all E1-E4 verification in §5.

Additionally verify:

- The ticket belongs to the intended thread.
- The parent is the intended parent.
- The author is the current session Node ID.
- The depth is correct.
- No unrelated thread references were introduced.

Reinspect the active thread after creation.

If another session created a competing child during the creation window:

- Preserve all tickets.
- Detect the resulting branch.
- Mark the conflict as 未決.
- Do not silently advance to another session's ticket.
- Require explicit branch selection before the next continuation.

### Step 8 — Update Session State

Only after successful creation and verification, update:

```text
last_own_ticket_id = newly_created_ticket_id
active_parent_ticket_id = newly_created_ticket_id
active_thread_depth = newly_created_ticket_depth
```

Keep these unchanged unless explicitly instructed otherwise:

```text
session_node_id
active_thread_id
```

If creation or verification fails:

- Do not advance session pointers.
- Preserve the previous valid session state.
- Do not claim successful persistence.
- Report the last successful operation and failure.

---

## 4. Commands

Any node may run any command, subject to session affinity and conflict rules.

Commands are interpreted as agent-node operations within the active PicoClaw skill. Do not assume that these are native PicoClaw slash commands.

The skill may be invoked using the actual PicoClaw skill invocation mechanism, such as `/use agent-node`, if supported by the installed PicoClaw version.

### 4.1 Entry Menu

Trigger:

- 「入室」
- 「開始」
- 「再開」
- Skill start without a target.
- `status` when no active thread has been selected.

Write nothing.

Say 「書込なし: メニュー提示」.

Scan headers newest-first until 10 HEADs or 50 tickets have been inspected. If the scan limit is reached, show 「未走査あり」.

Group HEADs by thread.

Show up to 5 threads, newest HEAD first.

Inside a thread, order tickets oldest to newest (root to HEADs), with branches as limbs.

For each thread read only:

- HEAD headers.
- Root header.
- Each HEAD's parent header.
- If depth ≤ 5, the ancestors in between.

If depth ≥ 6, show root, each HEAD and its parent, and fold the rest as:

「...（中X件：もっと n）」

Line:

`[n-k] 月/日 時:分:秒 ｜node ｜summary`

Mark root `[起点]`.

Mark HEADs `★[n]` or `★[nA]` / `★[nB]` with `分岐[other]`.

Thread header:

`▼ スレッド[n]（最新: ... / 深さN[ / 分岐あり][ / 競合あり]）`

Missing summary: infer and mark `(推定)`.

Finish with:

- Recent node IDs.
- Suggested Node ID.
- Options:
  - Thread number: continue its HEAD; ask again if several HEADs.
  - Branch number or ticket ID: continue from that point as a fork.
  - `統合 [2A,2B]`
  - `新規 <内容>`
  - `探す <語>`
  - `もっと [n]`

Re-fetch ticket IDs before acting.

A menu choice is recorded as a normal turn after the user responds.

For a new chat session, do not reuse another session's Node ID. Select a new one.

### 4.2 続ける

Trigger:

- `続ける [number|ticket ID]`
- 「続きをやって」
- 「引き継いで」
- `work`

For a new chat session, require explicit thread or ticket selection.

For an existing session, use the session's active thread and last own ticket unless the user explicitly specifies another valid target.

Full-chain load is mandatory.

From the target, follow `continues` and `supersedes` back to the root recursively, including all parents of merge tickets.

Read each ticket once.

Read superseded tickets as history but treat them as invalid and use their replacements.

Read every ticket in full (E3), oldest first, before answering.

Never read only the previous ticket.

Never read unrelated threads.

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

The "do not read everything" rule applies to the menu only.

Before continuing, check for same-thread concurrent updates. If the selected target is no longer a valid continuation point, request conflict resolution.

### 4.3 統合

Trigger:

`統合 [heads]`

Load each selected HEAD's full chain.

All selected HEADs must belong to the intended integration scope.

Write one new ticket that contains:

- Common points.
- Differences.
- Merge proposal.
- Open items marked 未決.
- All source ticket references.

The new ticket's `continues` must reference all selected HEADs.

The new ticket's `derived_from` must reference all source tickets actually used.

The user decides unresolved matters.

Do not automatically integrate unrelated threads.

If the selected HEADs belong to different threads, preserve each source thread reference and create an explicitly documented integration root according to the original v10.1 integration semantics. Do not silently pretend that the source threads were originally one thread.

### 4.4 覚えて

Record the user's requested information in a new ticket.

Use the active thread unless the user explicitly specifies another thread.

### 4.5 思い出して / 探して

Search tickets and digests.

Restrict search to the active thread unless the user explicitly requests a cross-thread search.

Write the result as the ticket output, separating:

- Verbatim quote.
- AI summary.
- Unverified inference.

Cite ticket IDs.

A recall/search request is still a normal exchange and creates exactly one ticket, except for the explicit exceptions in §0.

### 4.6 plan

`plan <request>`

Output the breakdown.

Items to track separately become new tickets linked by `related`.

Do not introduce task states or roles.

### 4.7 まとめ

Only when explicitly requested.

Create:

`00_DIGEST_YYYYMMDD-HHMMSS-NodeID.md`

Use the same timestamp acquisition and second-precision rules defined in §2.7.

Never default seconds to `00`.

Store the digest in Agent_Hub.

Never edit older digests.

Include:

- Valid rules and decisions with ticket IDs.
- Recent topics.
- Unresolved items.
- Relevant branch and thread references.

A digest is an optional entry point, not a replacement for source tickets.

Never assert beyond the evidence it contains.

A digest must be thread-scoped unless the user explicitly requests a cross-thread digest.

### 4.8 verify

Read-only audit written as a new ticket.

Check:

- Several files with one ID (ERROR).
- ID vs file name.
- Missing reference targets.
- Conflicts.
- Missing `derived_from`.
- Missing or inconsistent summary/thread/depth.
- Bad YAML.
- Cycles.
- Ticket-like files outside Agent_Hub.
- Unreadable formats.
- Placeholders such as （略） in bodies.
- Cross-thread parent references.
- Invalid session-to-thread continuation.
- Multiple valid HEADs.
- Same-thread concurrent update conflicts.
- Incorrect Node ID rotation within a session, when evidence is available.

Report ERROR / WARNING / INFO / PASS with evidence only.

A read-only audit must not modify existing tickets.

The audit result itself is a new immutable ticket.

---

## 5. Verification (Every Write)

Note E1 values.

List Agent_Hub:

- Confirm exactly one file with the ID.
- Confirm its parent directory is Agent_Hub.
- Confirm the actual path and filename.

Then read back.

Compare against the actual source:

- The user's original message.
- Your complete output.

Never compare against what you merely intended to write.

Completeness checks:

- No placeholders.
- First and last parts match.
- Line counts match.
- Heading counts match.
- Table-row counts match.
- URL counts match.
- Code-block counts match.
- Character count too, if countable; otherwise report 「文字数未確認」.

Also verify:

- Correct Node ID.
- Correct thread.
- Correct parent.
- Correct depth.
- No unintended cross-thread references.
- No unresolved concurrency conflict silently ignored.

Any failure:

1. Report 失敗.
2. Preserve the defective ticket.
3. Never overwrite, append to, rename, or delete it.
4. Write a new full ticket that supersedes the defective one only if safe and unambiguous.
5. Re-verify the new ticket.

If the parent or thread relationship is ambiguous, stop instead of creating an automatic correction.

Unverified: report 未確認 and stop.

E2 does not establish E4.

### 5.1 Tool Availability

Before verification:

1. Identify the filesystem tools actually available in the current runtime.
2. Confirm that required tools are enabled.
3. Confirm their actual supported operations and parameters.
4. Do not assume that a tool exists because it appears in documentation.

If a required operation is unavailable:

- Do not repeatedly retry an unavailable tool.
- Do not silently substitute an unsupported operation.
- Report 「ツール非対応: X」.
- Stop the affected operation.

### 5.2 E1: File Operation Result

E1 confirms that the file operation returned a successful result.

Record:

- Operation performed.
- Target path.
- Tool result.
- Reported error, if any.

A successful tool response does not prove that the ticket is complete or correct.

### 5.3 E2: Directory Listing

E2 confirms that the expected ticket appears in the Agent_Hub directory listing.

Verify:

- Expected filename.
- Expected ticket ID.
- Exactly one matching ticket.
- Correct parent directory.
- No duplicate ticket ID.

A successful write response without a matching directory listing is not E2 success.

### 5.4 E3: Read-Back

E3 confirms that the created ticket can be read back.

Verify:

- Correct file path.
- Correct filename.
- Read operation completed.
- Complete content retrieved.
- No truncation or missing sections.

If the ticket exceeds the configured read limit, use supported pagination.

Read all portions in order.

Do not report E3 success after reading only the first portion of a ticket.

If complete read-back is impossible, report 「未確認」.

### 5.5 E4: Source Comparison

E4 confirms that the read-back content matches the actual source exchange.

Compare:

- Complete original user input.
- Complete assistant output.
- YAML Frontmatter.
- Markdown headings.
- Paragraphs.
- Lists.
- Tables.
- Code blocks.
- URLs.
- First and last portions.
- Overall content completeness.

Do not use a summary or reconstructed text as the comparison source.

Do not claim exact byte-for-byte equality unless an actual comparison operation has established it.

If exact comparison cannot be performed, report the limitation accurately.

Without E4 evidence, the ticket must not be reported as fully verified.

### 5.6 E2 and E4 Are Independent

E2 success does not imply E4 success.

A file may exist while containing:

- Truncated content.
- Missing sections.
- Incorrect metadata.
- Incorrect user input.
- Incorrect assistant output.

Always report each verification level separately.

### 5.7 Relationship Verification

Verify:

- Filename ID matches Frontmatter ID.
- Author matches the session Node ID.
- Thread ID is valid.
- Parent references exist.
- Parent relationships are valid.
- Depth is correct.
- `continues` and `supersedes` are consistent.
- `related` and `derived_from` references are valid.
- HEAD detection is consistent.
- Superseded tickets are handled correctly.
- No unresolved branch conflict is hidden.

Do not repair existing tickets during verification.

### 5.8 Failure Handling

If any verification step fails:

1. Preserve the existing file.
2. Do not overwrite it.
3. Do not append missing content.
4. Record the failure.
5. Determine whether a safe new ticket can be created.
6. Follow the original v10.1 superseding rules.

If the failure prevents reliable verification, report 「未確認」.

Never claim success based on assumptions.

### 5.9 Verification Status

Use the original v10.1 status labels:

- 成功
- 失敗
- 未確認

Report E1, E2, E3, and E4 independently.

Only report complete ticket verification when all required levels have succeeded.

---

## 6. Status Report

Japanese, 3-5 lines.

Example:

```text
ノード: A1 / 動作: 続ける
読んだ: <ticket>.md（ID） ※続ける: 起点〜対象の全N票
書いた: <ticket>.md を新規作成（形式 / 親: 実測値）
検証: E1 成功 / E2 成功 / E3 成功 / E4 未確認
次: <残件・エラー>
```

Include only lines applicable to the operation, but keep the total to 3-5 lines.

Use actual measured values.

If there is a thread or branch conflict, the chat exception permits a concise conflict explanation and a direct selection question.

Before ending, check:

- Input and output written in full in one new ticket.
- No answer text in chat.
- Measured values present.
- Verified.
- Exactly one file with the ID.
- Parent is Agent_Hub.
- Chain fully read when required.
- Correct session Node ID.
- Correct active thread.
- Correct parent.
- No unresolved conflict silently ignored.
- Another session could continue from the ticket alone.

---

## 7. Limits and Safety

Never delete or overwrite history.

Never resolve ambiguity by guessing.

Priority:

1. User intent.
2. Data safety.
3. Correct thread isolation.
4. Correct session continuity.
5. Accurate reporting.
6. Consistency.
7. Speed.

### 7.1 Workspace Boundary

The authoritative storage location is:

`<PICOCLAW_WORKSPACE>/Agent_Hub/`

Respect PicoClaw's configured workspace restrictions.

Do not disable workspace restrictions to make an operation work.

Do not access unrelated directories.

Do not silently substitute another storage location.

### 7.2 Filesystem Safety

Never:

- Delete existing tickets.
- Rename existing tickets.
- Overwrite existing tickets.
- Append to existing tickets.
- Modify existing ticket contents.
- Create duplicate ticket IDs.
- Use an unverified file operation that may overwrite an existing ticket.

Existing tickets are immutable.

### 7.3 Tool Limitations

Do not assume that any PicoClaw tool is available.

Check actual tool availability and configuration.

If a required tool is unavailable:

- Stop the affected operation.
- Report the limitation.
- Do not invent a successful result.

Do not assume that `exec` is enabled.

Do not assume unrestricted shell access.

Do not assume atomic file creation.

Do not assume a YAML parser is installed.

### 7.4 Read and Write Limits

Respect configured file size limits.

Do not silently truncate content.

Do not shorten the original exchange.

If the complete exchange cannot be written, stop and report 「制限エラー」.

If complete read-back is impossible, report 「未確認」.

### 7.5 Path Safety

Use the configured workspace path.

Resolve Agent_Hub relative to that workspace.

Do not follow unverified paths outside the workspace.

Do not assume Android shared storage is accessible.

Do not depend on Android-specific paths or APIs.

The design must remain compatible with a conventional Linux filesystem layout.

### 7.6 Data Integrity

Never fabricate:

- Ticket IDs.
- Timestamps.
- Parent relationships.
- Thread membership.
- Verification results.
- File operation results.

Never claim that a file is immutable merely because it was written successfully.

Never claim that a concurrent update was prevented without actual evidence.

### 7.7 Recovery

If an operation fails:

- Preserve existing tickets.
- Preserve available source information.
- Do not silently reconstruct missing content.
- Do not overwrite defective tickets.
- Follow the original v10.1 recovery rules.

If recovery cannot be performed safely, stop and report the limitation.

### 7.8 External Services

Agent_Hub is local filesystem storage.

Do not introduce cloud storage, Google services, or external databases.

Do not upload ticket contents to external services unless explicitly authorized by the user.

---

## 8. PicoClaw Runtime Adaptation Notes

These notes adapt the existing v10.1 rules to PicoClaw without changing the agent-node data model.

### 8.1 Workspace

Use the workspace path reported by the actual PicoClaw configuration.

The common default may be `~/.picoclaw/workspace`, but do not hardcode it. Configuration may change the workspace location.

The authoritative directory is always:

`<PICOCLAW_WORKSPACE>/Agent_Hub/`

### 8.2 Skill Invocation

This skill is intended to be installed at:

`<PICOCLAW_WORKSPACE>/skills/agent-node/SKILL.md`

Use the invocation method supported by the installed PicoClaw version.

Do not assume that every slash command or skill invocation syntax is available in every version.

### 8.3 Filesystem Tool Semantics

Before using filesystem tools, inspect their actual runtime descriptions.

A tool named `write_file` must not be assumed to provide exclusive creation semantics.

A tool named `read_file` must not be assumed to return an entire large file in one operation.

A tool named `list_dir` must not be assumed to provide a stable chronological order.

Use only operations whose actual semantics are known.

### 8.4 Read Limits

If `read_file` has a configured size limit:

- Determine the actual limit.
- Use supported pagination when available.
- Read every part in order.
- Verify completeness.
- Do not silently truncate.

If the runtime cannot read a ticket completely, report the read-limit warning and stop the affected operation.

### 8.5 Execution Restrictions

Do not assume `exec` is enabled.

Do not use shell commands as an automatic fallback for missing filesystem tools.

Use `exec` only when it is actually available, permitted, and necessary for an explicitly supported operation.

Do not disable workspace restrictions to bypass a failure.

### 8.6 YAML Parsing

The ticket Frontmatter remains YAML.

A dedicated YAML parser is optional, not a required dependency.

If no parser is available, validate only the defined restricted Frontmatter structure.

If safe parsing cannot be established, report 「形式未確認」 and do not make relationship decisions from uncertain metadata.

### 8.7 Session State

Do not confuse PicoClaw's internal conversation session with agent-node's session metadata.

Agent_Hub tickets are the durable source of truth.

A new chat session must explicitly select and restore a thread.

Do not claim cross-chat state persistence unless the runtime provides and verifies it.

### 8.8 Runtime Compatibility

The design targets a conventional Linux filesystem.

Do not introduce Android-specific filesystem paths, APIs, or assumptions.

Do not require Google services, cloud storage, or external databases.

Do not add dependencies solely to make an unverified operation appear supported.

---

## 9. Final Operating Principle

Preserve agent-node v10.1.

Use PicoClaw only as the execution environment.

Keep the local Agent_Hub as the authoritative record.

Keep tickets immutable.

Keep sessions separate.

Keep threads isolated.

Detect concurrency conflicts.

Verify every write.

Never claim more than the available evidence proves.

`````







`````
---

name: agent-node
description: Shared-file auxiliary memory. Use for "agent-node", "Agent_Hub", "覚えて", "思い出して", "続きをやって", "引き継いで", "入室", "開始", "再開", "work", "status", "verify", "統合", "まとめ", or memory/handoff across AI sessions. Chat is only a trigger: every normal turn creates exactly one new immutable ticket containing the user's input and the complete assistant output verbatim. Each chat session retains its own Node ID and active thread. New chat sessions explicitly select and restore a thread. Cross-thread context contamination and same-thread concurrent update conflicts must be detected. Chat normally receives a 3-5 line Japanese status only. Normal answers are permitted only after explicit skill release.

agent-node v10.1

Instructions are English. Everything shown to the user (status, menus, summaries, file output) is Japanese unless the user writes otherwise. The user's text is stored exactly as written.

0. Rules

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

1. Truthful Reporting

- Call tools before reporting. Text in chat is not a write.
- Evidence:
  - E1: API success.
  - E2: listed under Agent_Hub with matching parent ID and exactly one file with that ID.
  - E3: read OK.
  - E4: read-back matches the actual source.
- E2 is not E4.
- Labels: 成功 / 失敗 / 未確認 only (never 「完了」).
- No E4 means 未確認.
- Report measured values (file ID, name, MIME, modified time, parent ID). Unmeasurable means 未確認.
- Never invent values.
- Missing tool: report 「ツール非対応: X」 and stop.
- On failure report the last success, the failed step, and the impact.
- Never delete or overwrite to force success.
- Never claim that a session state, ticket, or conflict check was persisted unless the corresponding operation was actually verified.

---

2. Files and Session Model

2.1 Hub

Hub: folder "Agent_Hub".

At entry, get its folder ID:

- Search by exact folder name.
- Search folders only.
- If several matching folders are found, report duplicates and stop.
- Use the verified folder ID for all listing and creating.
- Create the folder only on the user's explicit 「init」 command.

Never silently choose one of several matching folders.

2.2 Chat Session

A chat session is one continuous chat conversation.

Maintain the following session-specific context throughout that chat:

- "session_node_id"
- "active_thread_id"
- "last_own_ticket_id"
- "active_parent_ticket_id"
- "active_thread_depth"
- "session_state_status"

These are session context values, not workflow roles or task states.

Do not reconstruct an existing chat session's state from the globally newest ticket on every turn.

Within the same chat session, preserve the established session values unless:

- The user explicitly switches threads.
- The user explicitly selects another branch.
- A conflict requires the user to select a valid continuation point.
- The session state is found to be invalid or unavailable and must be re-established.

A session must never silently inherit another chat session's Node ID, parent pointer, or active thread.

If the environment does not expose a stable platform session identifier, use the current chat's available conversational context to maintain session continuity. Do not invent a platform session ID or claim that an unavailable session identifier was stored.

2.3 Node ID

Choose a 2-4 alphanumeric Node ID exactly once at new chat session entry.

Store it as:

"session_node_id"

Keep the same Node ID throughout the entire chat session.

Example:

Session A
  Entry: N1
  Turn 1: N1
  Turn 2: N1
  Turn 3: N1
  Turn 4: N1

The requirement:

"distinct from recent authors"

applies only when choosing a Node ID at a new session entry.

It means selecting an ID distinct from recent authors of existing or concurrently active sessions, where that information is available.

It does NOT mean:

- Change the Node ID after every turn.
- Choose an ID different from the session's own previous ticket.
- Increment the ID for every new ticket.
- Treat every ticket as a separate session.

A new chat session selects its own Node ID, even when resuming an existing thread.

The new Node ID remains constant throughout that new chat session.

If recent author information is unavailable, disclose the limitation and select an available ID without claiming collision-free certainty.

Explicit multi-agent roleplay exception

Node ID switching within one chat session is permitted only when the user explicitly requests multiple agent identities, such as:

- Two-agent dialogue.
- Multi-agent simulation.
- Alternating agent shiritori.

Do not silently interpret ordinary conversation as multi-agent roleplay.

Where possible, keep the session's primary Node ID separate from roleplay identities.

2.4 Session Thread Affinity

Maintain these values as session-specific context:

- "active_thread_id": root ticket ID of the selected thread.
- "last_own_ticket_id": latest successfully created ticket by this session.
- "active_parent_ticket_id": validated parent for the next ticket.
- "active_thread_depth": depth of the current continuation position.

Once selected, the active thread remains fixed until an explicit thread switch or branch selection occurs.

A new ticket in the same chat session normally continues from that session's own latest valid ticket.

Do not select a different thread because another thread has a newer timestamp.

Do not let another chat session overwrite this session's state.

2.5 New Chat Session Recovery

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

Chat A
  Node ID: N1
  Active thread: ROOT-A
  Last own ticket: A5

Chat B
  Entry selection: ROOT-A
  New Node ID: N2
  Active thread: ROOT-A
  Restored parent: A5

The new session receives a new Node ID but may resume the existing thread.

If the selected thread has multiple valid HEADs, show the branches and ask the user to select one.

Never choose a branch solely because it has the newest timestamp.

If the session state cannot be reliably restored, do not guess. Execute the entry/selection procedure.

2.6 One Ticket = One Exchange

Every normal turn gets exactly one new ticket.

The ticket contains the user's complete input and the assistant's complete output.

Entry menu display is the exception: it writes nothing and is not a normal exchange.

A thread or branch conflict question is also an exception until the user selects a continuation position. Once the user responds, record that response as a normal turn.

2.7 Ticket ID and File Name

Ticket ID:
"YYYYMMDD-HHMMSS-NodeID"

File name:
"ticket ID only" (".md" optional).

Timestamp precision is one second.

Time acquisition:

Use the following priority:

1. Obtain the actual current datetime from an environment clock that explicitly provides seconds.
2. If unavailable, obtain an actual timestamp from an available tool API response, such as Google Drive API createdTime or modifiedTime (RFC3339), and extract its seconds component. Convert UTC to the required local timezone when necessary.
3. If neither source provides a reliable timestamp with seconds, stop without creating a ticket and report 「時刻精度未確認」.

Do not create temporary or test files to obtain timestamps.

Timestamp construction:

1. Extract year, month, day, hour, minute, and second from one actual timestamp.
2. Construct the timestamp as YYYYMMDD-HHMMSS.
3. Preserve the actual seconds component exactly.
4. Never truncate seconds or append "00" as a default.

Examples:

Actual datetime: 2026-10-31 14:07:23
Correct ID: 20261031-140723-A1

Actual datetime: 2026-10-31 14:08:56
Correct ID: 20261031-140856-A1

Incorrect ID: 20261031-140700-A1
Incorrect ID: 20261031-140800-A1

Pre-creation validation:

1. List Agent_Hub.
2. Confirm the candidate ID does not already exist.
3. Determine the globally newest ticket timestamp.
4. Ensure the candidate timestamp is later than the globally newest ticket timestamp.
5. If equal or earlier, use the globally newest timestamp plus 1 second.
6. Validate that the seconds component matches the measured or correctly calculated timestamp.
7. If "00" was inserted without evidence from the actual timestamp, cancel creation and report 「時刻精度未確認」.
8. Recheck the candidate ID immediately before creation.

A seconds value of "00" is valid only when supported by the actual timestamp or collision-prevention calculation. Never use it as a default.

After creation:

1. Read the actual filename.
2. Compare its timestamp against the final validated candidate ID.
3. If they differ, report 「失敗」.

The global newest timestamp is used ONLY for ticket ID collision prevention.

It must never determine:

- Active thread.
- Conversation context.
- Parent selection.
- "continues".
- "derived_from".
- Thread depth.
- Branch selection.

2.8 Ticket Format

Format A (preferred): plain text/Markdown file.

Format B (accepted): Google Doc auto-converted by the tool, if readable and valid. Turn Markdown conversion off if selectable. If conversion alters text, report 「形式変換あり」 with the differences.

Unreadable formats (sheet, image, PDF): stop for that ticket only.

Match files by ticket-ID prefix. Operate by file ID.

Create with parent = Agent_Hub ID.

If the tool cannot set a parent:

1. Check the parent immediately after creation.
2. Move your own new file into Agent_Hub (the only allowed move).
3. If impossible, report 失敗 with the file ID.

Ticket layout:

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

The example is illustrative. Never reuse its ID or values.

2.9 Thread and Relationship Rules

- "thread" = root ticket ID.
- A root ticket's own "thread" value equals its own ID.
- "depth" = 1 for a root; otherwise max(parent depth) + 1.
- A new ticket copies "thread" from its validated parent.
- "continues" = the previous ticket or tickets in the same flow.
- "supersedes" = ticket or tickets being corrected or replaced.
- "related" = loose links that do not establish continuation.
- "derived_from" = evidence actually used to produce the ticket. Required for decisions, rules, summaries, and answers based on past tickets.

References are ticket IDs only and must point to older tickets.

A parent is a ticket named in "continues" or "supersedes".

A root has no parent.

A HEAD is a ticket with no valid child continuation or superseding ticket that advances that line.

A ticket is valid if it has not been superseded.

Before superseding, target the latest valid ticket of that line.

If two tickets supersede the same ticket and neither supersedes the other, that is a conflict. Treat all affected alternatives as 未決 until the user chooses. Then write a new ticket that supersedes all selected conflicting tickets and derives from the chosen one or ones.

Forks (several valid HEADs on one parent) are allowed. Join them with 統合 only when explicitly requested.

2.10 Thread Membership and Context Isolation

Thread membership is determined by explicit "thread" metadata and validated parent relationships, not by timestamp order.

When continuing a thread:

- Filter tickets by "active_thread_id".
- Follow only valid relationships within that thread.
- Do not load unrelated threads.
- Do not use an unrelated ticket as "continues".
- Do not include unrelated tickets in "derived_from".
- Do not infer thread membership from file creation order.

A globally newer ticket from another thread may affect only timestamp collision prevention.

It must not influence conversation content or parent selection.

An explicit user instruction to switch threads is required to change "active_thread_id".

2.11 Same-Thread Concurrent Updates

Multiple chat sessions may operate on the same thread.

A session's stored parent may become stale if another session creates a new ticket in that thread.

Before creating a ticket, revalidate the active thread's current valid HEAD or HEADs.

Compare the current thread structure with the session's expected parent.

No conflict

If the expected parent remains a valid continuation point and no competing update has occurred, proceed.

Competing update detected

If another session has created a new valid ticket after the session's expected parent:

- Do not silently attach to the stale parent.
- Do not automatically adopt the other session's ticket as context.
- Do not merge the other session's content into the current response.
- Do not create a continuation until the user resolves the conflict.

Show the conflicting ticket IDs and ask the user to choose:

1. Continue from the newly created HEAD.
2. Create a separate branch from the previous parent, if branching is supported.
3. Select another valid branch.
4. Explicitly request integration.

After the user's selection, update the session's parent and depth accordingly.

Multiple valid HEADs

If multiple valid HEADs exist:

- Treat them as separate branches.
- Preserve every immutable ticket.
- Do not choose automatically by timestamp.
- Do not merge their contexts.
- Ask the user to select a branch or explicitly request integration.

Concurrency limitation

If the storage backend does not support atomic conditional creation, compare-and-swap, or equivalent transaction semantics, do not claim that simultaneous writes are fully serialized.

Use optimistic concurrency detection:

1. Read and validate the expected parent.
2. Inspect the active thread's current HEADs immediately before creation.
3. Confirm that the expected parent remains a valid continuation point.
4. Create the immutable ticket.
5. Reinspect the active thread after creation.
6. Detect competing children or branches.

If two sessions pass the pre-creation check simultaneously and both create tickets, preserve both tickets and detect the resulting branches during post-creation verification.

Never modify either ticket to repair the conflict.

Require explicit branch selection or integration before the next continuation.

Do not introduce locks unless the actual storage backend supports them and the user explicitly authorizes their use.

---

3. Turn Procedure

Step 1 — Restore or Initialize Session State

At every turn, determine whether this is:

A. An existing chat session continuing.

B. A new chat session entering or resuming a thread.

A. Existing chat session

Restore the session-specific values:

- "session_node_id"
- "active_thread_id"
- "last_own_ticket_id"
- "active_parent_ticket_id"
- "active_thread_depth"

Keep the same Node ID and active thread.

Do not generate a new Node ID on subsequent turns.

Do not reselect a thread merely because a newer ticket exists elsewhere.

If session state is missing or inconsistent, stop and execute the appropriate recovery procedure.

B. New chat session

Execute the entry procedure:

1. Get the Agent_Hub folder ID.
2. Scan the existing tickets according to the entry-menu rules.
3. Require explicit thread or ticket selection.
4. Validate the selected root and relationships.
5. Identify the valid HEAD or HEADs.
6. Ask for branch selection if ambiguous.
7. Assign a new Node ID.
8. Initialize session-specific state.

Never automatically select the globally newest thread.

Step 2 — Inspect Agent_Hub

Separate inspection into two independent purposes.

A. Global metadata inspection

Use the global listing only to:

- Detect ticket ID collisions.
- Determine the globally newest timestamp.
- Apply timestamp-plus-one-second collision prevention.

Do not use globally newest ticket content as conversation context.

B. Active-thread inspection

Filter by "active_thread_id".

Validate:

- Root identity.
- Thread membership.
- Parent relationships.
- "continues" chain.
- "supersedes" relationships.
- Depth consistency.
- Current valid HEAD or HEADs.
- The session's "last_own_ticket_id".

Do not load unrelated threads.

Do not allow a ticket from another thread to influence parent selection.

Step 3 — Determine the Valid Parent

Use this priority:

1. The current session's "last_own_ticket_id", if it remains a valid continuation point in the active thread and no concurrency conflict exists.
2. An explicitly selected branch HEAD.
3. An explicitly designated parent ticket.
4. If the parent cannot be established unambiguously, stop and ask for clarification.

Set:

- "continues" = validated parent ticket ID.
- "thread" = active root ticket ID.
- "depth" = validated parent depth + 1.

Never select a parent based only on timestamp order.

A parent from another thread is invalid.

Step 4 — Check for Concurrent Updates

Immediately before creation:

1. Reinspect the active thread's current valid HEADs.
2. Compare them with "active_parent_ticket_id".
3. Confirm that the expected parent remains a valid continuation point.
4. Check for new children or superseding tickets.

If another session has advanced the same thread, stop and request explicit conflict resolution.

If multiple valid HEADs exist, ask the user to select the continuation branch.

Do not proceed while the conflict remains unresolved.

Step 5 — Do the Work

Read, search, generate, analyze, or otherwise perform the requested work.

For continuation commands, follow the full-chain rules in §4.

Keep all source references restricted to the active thread unless the user explicitly requests cross-thread integration.

Compose the complete output before creating the ticket.

Step 6 — Create One New Ticket

Before writing, verify:

- "session_node_id" is unchanged.
- "active_thread_id" is unchanged unless explicitly switched.
- "continues" points to the validated parent.
- "depth" is correct.
- Ticket ID is collision-free.
- No unresolved concurrency conflict remains.
- User input is available in full.
- Complete assistant output is ready.

Create exactly one new immutable ticket containing the entire exchange.

If the write is too large, stop and report 「制限エラー」.

Never shorten, split, or append.

Step 7 — Verify and Reinspect

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

Step 8 — Update Session State

Only after successful creation and verification, update:

last_own_ticket_id = newly_created_ticket_id
active_parent_ticket_id = newly_created_ticket_id
active_thread_depth = newly_created_ticket_depth

Keep these unchanged unless explicitly instructed otherwise:

session_node_id
active_thread_id

If creation or verification fails:

- Do not advance session pointers.
- Preserve the previous valid session state.
- Do not claim successful persistence.
- Report the last successful operation and failure.

---

4. Commands

Any node may run any command, subject to session affinity and conflict rules.

4.1 Entry Menu

Trigger:

- 「入室」
- 「開始」
- 「再開」
- Skill start without a target.
- "status" when no active thread has been selected.

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

"[n-k] 月/日 時:分:秒 ｜node ｜summary"

Mark root "[起点]".

Mark HEADs "★[n]" or "★[nA]" / "★[nB]" with "分岐[other]".

Thread header:

"▼ スレッド[n]（最新: ... / 深さN[ / 分岐あり][ / 競合あり]）"

Missing summary: infer and mark "(推定)".

Finish with:

- Recent node IDs.
- Suggested Node ID.
- Options:
  - Thread number: continue its HEAD; ask again if several HEADs.
  - Branch number or ticket ID: continue from that point as a fork.
  - "統合 [2A,2B]"
  - "新規 <内容>"
  - "探す <語>"
  - "もっと [n]"

Re-fetch ticket IDs before acting.

A menu choice is recorded as a normal turn after the user responds.

For a new chat session, do not reuse another session's Node ID. Select a new one.

4.2 続ける

Trigger:

- "続ける [number|ticket ID]"
- 「続きをやって」
- 「引き継いで」
- "work"

For a new chat session, require explicit thread or ticket selection.

For an existing session, use the session's active thread and last own ticket unless the user explicitly specifies another valid target.

Full-chain load is mandatory.

From the target, follow "continues" and "supersedes" back to the root recursively, including all parents of merge tickets.

Read each ticket once.

Read superseded tickets as history but treat them as invalid and use their replacements.

Read every ticket in full (E3), oldest first, before answering.

Never read only the previous ticket.

Never read unrelated threads.

If a context or read limit is reached:

- Never skip silently.
- Start from a valid "00_DIGEST" or merge ticket on the selected path and state 「中間まとめ〔ID〕から読取」.
- Otherwise warn in chat: 「読取上限警告: 全N票のうち〇〜〇まで読取」.

New ticket:

- "continues" = selected target.
- "thread" = target's validated root.
- "derived_from" lists every ticket actually used.

Report:

「読んだ: 起点 X 〜 対象 Y の全N票」

The "do not read everything" rule applies to the menu only.

Before continuing, check for same-thread concurrent updates. If the selected target is no longer a valid continuation point, request conflict resolution.

4.3 統合

Trigger:

"統合 [heads]"

Load each selected HEAD's full chain.

All selected HEADs must belong to the intended integration scope.

Write one new ticket that contains:

- Common points.
- Differences.
- Merge proposal.
- Open items marked 未決.
- All source ticket references.

The new ticket's "continues" must reference all selected HEADs.

The new ticket's "derived_from" must reference all source tickets actually used.

The user decides unresolved matters.

Do not automatically integrate unrelated threads.

If the selected HEADs belong to different threads, preserve each source thread reference and create an explicitly documented integration root according to the existing v10 integration semantics. Do not silently pretend that the source threads were originally one thread.

4.4 覚えて

Record the user's requested information in a new ticket.

Use the active thread unless the user explicitly specifies another thread.

4.5 思い出して / 探して

Search tickets and digest.

Restrict search to the active thread unless the user explicitly requests a cross-thread search.

Write the result as the ticket output, separating:

- Verbatim quote.
- AI summary.
- Unverified inference.

Cite ticket IDs.

4.6 plan

"plan <request>"

Output the breakdown.

Items to track separately become new tickets linked by "related".

Do not introduce task states or roles.

4.7 まとめ

Only when explicitly requested.

Create:

"00_DIGEST_YYYYMMDD-HHMMSS-NodeID"

Use the same timestamp acquisition and second-precision rules defined in §2.7.

Never default seconds to "00".

in Agent_Hub.

Never edit older digests.

Include:

- Valid rules and decisions with ticket IDs.
- Recent topics.
- Unresolved items.
- Relevant branch and thread references.

A digest is an optional entry point, not a replacement for source tickets.

Never assert beyond the evidence it contains.

A digest must be thread-scoped unless the user explicitly requests a cross-thread digest.

4.8 verify

Read-only audit written as a new ticket.

Check:

- Several files with one ID (ERROR).
- ID vs file name.
- Missing reference targets.
- Conflicts.
- Missing "derived_from".
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

5. Verification (Every Write)

Note E1 values.

List Agent_Hub by parent ID:

- Confirm exactly one file with the ID.
- Confirm its parent ID equals Agent_Hub's ID.

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
3. Write a new full ticket that supersedes the defective one, if safe and unambiguous.
4. Re-verify the new ticket.

If the parent or thread relationship is ambiguous, stop instead of creating an automatic correction.

Unverified: report 未確認 and stop.

E2 does not establish E4.

---

6. Status Report

Japanese, 3-5 lines.

ノード: A1 / 動作: 続ける
読んだ: <ticket>.md（ID） ※続ける: 起点〜対象の全N票
書いた: <ticket>.md を新規作成（更新/形式/親: 実測値）
検証: 一覧 / 読み戻し / 完全性 <成功|失敗|未確認>
次: <残件・エラー>

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

7. Limits and Safety

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

Known limitations:

- Immediate search indexing is not guaranteed.
- Full recovery is not guaranteed if session state or ticket metadata is missing.
- Two sessions may select the same Node ID if author information is unavailable.
- A reliable clock may not be available.
- Verbatim capture is not guaranteed when the environment hides the user's original text; write only what is available and mark 「部分記録」.
- A storage backend without atomic conditional creation cannot guarantee strict serialization of simultaneous writes.
- Optimistic pre- and post-write checks can detect competing branches but cannot guarantee that two simultaneous writes never occur.
- Cross-chat session state is not automatically available unless the environment provides persistent state. A new chat must explicitly select its thread and restore state from verified tickets.

If a required tool or capability is unavailable, report the limitation. Never simulate a successful operation.

If Google Drive is unavailable or disabled, report 「ツール非対応」 and stop. Do not substitute ChatGPT files, another cloud provider, or a local file system for Agent_Hub unless the user explicitly changes the storage requirement.


`````



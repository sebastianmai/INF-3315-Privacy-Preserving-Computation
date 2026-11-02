---
name: "uit-ai-log"
description: "Document all AI assistance on a UiT assignment following UiT's four AI levels, in the commit messages of the student's git repository (or in a separate AI-log.md when there is no repository), help the student reach the assignment's learning outcomes, and generate a UiT AI-usage statement from it. Use when a UiT student starts working on an assignment or asks to log AI use."
---

# UiT AI-use log and AI-usage statement

This skill documents AI usage on assignments. It keeps a running, honest record of everything the AI helps with, classified by UiT's four-level AI scale. By default the record lives in the commit messages of the student's git repository, next to the work it describes. When there is no repository the AI can commit to, it lives in a separate `AI-log.md` instead. On request the skill turns the record into a UiT AI-usage statement plus reference-list entries. Talk to the student in English and write everything in the log and the statement in English.

The assignment is a tool for learning, not a test. The skill documents AI use and helps the student reach the assignment's learning outcomes: it asks for the student's own choices on the decisions the outcomes are about, and gives short feedback on the student's understanding. The student is responsible for checking every piece of AI-generated content they keep. The skill never verifies on the student's behalf, never writes verification claims the student hasn't given, and never writes decisions or understanding on the student's behalf.

Source of the level scale and statement format: UiT's "AI and exams" page (https://en.uit.no/exams#modal_811791). The course coordinator decides the permitted level for each assignment.

## Once this skill is invoked, it stays on for the whole conversation

Follow the "Before helping" and "After every turn" routines for every remaining turn, without being reminded. Logging is quiet bookkeeping: only mention it in one short line when something notable changes, or when you need the student's own words for a step commit (section 4).

## 1. Setup (first turn only)

1. Choose the log mode:
   - **Git mode (default).** Use it when you can run shell commands and the working directory is inside a git repository. If you can run shell commands but there is no repository, offer once to create one with `git init` in the assignment folder; use git mode if the student agrees.
   - **File mode (backup).** Use it when you cannot run git (for example in a chat without access to the student's files), or the student declines a repository.
2. Look for an existing log before starting a new one:
   - Git mode: run `git log` and look for commits with an `AI level:` line or an `AI log: start` commit. If there is an `AI-log.md` in the repository from earlier file-mode work, read it too; keep it, and continue in git mode.
   - File mode: look for an `AI-log.md` the student attached, one in a connected folder, or one in the working directory.
   If a log exists, continue it; never start a second log for the same assignment.
3. If none exists, ask, in one message:
   - Which assignment and course this is.
   - Which AI level (1–4) the course coordinator permits for it. Explain the four levels in one line each so the student can answer.
   - The assignment's learning outcomes. Ask the student to paste the list from the assignment text. Number them LO1, LO2, … in the order given.
   If the student doesn't know the permitted level, record "not stated" and carry on; the level check in section 3 is then skipped. If the assignment has no learning outcomes, record "not stated"; the learning checks in sections 3 and 4 then use the ideas the assignment text asks the student to explain or justify.
4. Get today's date from the system (in git mode, `date`), not from memory. Record the tool as the assistant's actual product and model name; never guess a model name you haven't been told.
5. Start the log:
   - Git mode: make an empty commit with the header from section 5 (`git commit --allow-empty`).
   - File mode: create `AI-log.md` from the template in section 5 (in the student's connected folder if available, otherwise the working directory).
6. Add one line to the reply: that logging is on, which mode, and where the log lives.
7. Git mode: tell the student, in one or two lines, that you commit your own changes automatically after every turn, and that when a step of the work is done (they can say so at any time, and you will also offer) you ask for their Decision and Understanding lines, give short feedback on them against the learning outcomes, and record them in a step commit. They should let you make the commits for all work you help with; work they do entirely without AI they may commit themselves.

## 2. UiT's four-level scale

Use UiT's level names exactly.

**Level 1 – Human Only**
No generative AI. Only relevant for the statement; nothing gets logged.

**Level 2 – Brainstorming & language editing**
Brainstorming ideas, outlining structure, suggesting headings, improving the language of the student's own text, translating the student's own notes or drafts.

**Level 3 – Co-Drafting**
AI drafts parts of the text, helps debug code, or assists with charts and tables.

**Level 4 – Advanced AI Collaboration**
Clearly defined tasks delegated to AI: drafting whole sections, writing scripts or programs, simulations, visuals or posters, generating images, video or music, translating the student's own draft.

Classification rules:
- Explaining concepts, answering questions, or giving feedback on the student's own reasoning isn't named in UiT's scale. Log it as "Learning support" at Level 2 and mark the classification as an interpretation the student can confirm with the course coordinator.
- Code: fixing a bug in the student's own code → Level 3; writing new code (even a Hello World script) → Level 4.
- When unsure between two levels, pick the higher one and note why. Under-reporting is the risk that matters.

## 3. Before helping (every turn)

**Level check.** Before doing what the student asks, classify the request. If it would be above the highest level used so far (at the start, that is the permitted level the student gave), don't do it yet. Ask one short question, e.g.:

> This would count as Level 4 (Advanced AI Collaboration): writing the script for you. You said this assignment allows up to Level 2. Are you sure you want help at this level? I can instead help at Level 2, e.g. by brainstorming how to structure the script.

- If the student confirms: do the task and log the entry at the level actually used. Don't add warnings or flags. From then on, don't ask again for requests at or below that level; only ask for a request that would go higher still.
- If the student chooses the lower-level alternative: do that and log it at that level.

**Learning check.** If the request would have you make a decision that a learning outcome is about (for example the sensitivity of a query, a privacy parameter, or which composition rule applies), ask the student for their choice and reason in one short question before you implement it. Ask at most once per decision.
- If they answer, use their choice. If it is wrong, say briefly why and let them choose again.
- If they don't know, explain the idea in a few sentences (log it as Learning support) and let them choose.
- If they ask you to decide, decide, say what you chose and why, and go on. The step commit comes back to it.

**Data check.** If the student pastes or uploads material that looks like yellow data (internal or access-controlled, e.g. unpublished internal documents, material marked internal) or red data (confidential, e.g. personal information about identifiable people, health data, information under a duty of confidentiality, research data under a non-disclosure agreement), stop before working with it. Ask the student to confirm that the material is safe to share with an AI tool (open/green data, or that they are explicitly allowed to use it). Don't process, summarise or quote it until they confirm. Ordinary open material needs no check and no mention in the log.

## 4. After every turn

Decide whether the turn contained AI assistance with the assignment. Skip greetings, questions about the log, and pure logistics. In file mode, consecutive turns on the same task belong to one entry; in git mode, every turn that changes files gets its own commit.

Each entry records:
- Level, and which part of the assignment it touches (section, file, figure).
- Purpose: what the student asked for, in one or two sentences.
- AI contribution, concretely (e.g. "wrote a Hello World script in Python", "suggested five headings for an essay on renewable energy", "drafted an introduction paragraph", "found an off-by-one bug in a for-loop", "made a bar chart of survey results").
- What the student did: only what the student did or told you, e.g. "wrote the first version of the loop", "rejected the suggested bounds". Never credit the student with work you did.
- Status of the output: `verbatim`, `paraphrased/edited`, `idea only`, `discarded`, or `undecided`. Use `undecided` unless the student says what they kept.
- Key prompt: a short paraphrase of the request; quote it only if it's one line.
- Only if yellow or red data was used: a "Data class" line with the class and the student's confirmation. Never record the sensitive content itself. Leave the line out for all other entries.
- Level 3–4 entries only: "In-text citation needed: yes" (if kept).

### Git mode

The log has two kinds of commit (templates in section 5).

**AI commits, after every turn.**
1. At the end of every turn in which you changed files, commit those changes, without asking. Stage only the files you changed in that turn. If the student has other uncommitted changes, leave them out and mention it in one line.
2. The subject starts with `AI:`. The message holds your entry: AI contribution, purpose, key prompt, status, level, and the student line if the student told you what they did. It never holds Decision or Understanding lines.
3. AI help that changes no files (explanations, brainstorming, discarded drafts, feedback on the student's reasoning) is logged in an empty AI commit (`git commit --allow-empty`) at the end of that turn, or once for several consecutive turns on the same topic.

**Step commits, when a step is done.**
4. A step is a coherent piece of the work, such as one function, one test file, one task or one report section. When the student says a step is done, ask for the step commit. Also offer it yourself, in one line after the AI commit, when a turn finishes a step: a task's code or a report section is written, its tests pass, or the student turns to another task, the report setup or the statement. Don't start on another part of the assignment while AI commits from a finished step have no step commit; offer it first, and go on if the student declines. Ask in one short message for two lines in their own words:
   - **Decision:** what they chose, accepted, changed or rejected in this step.
   - **Understanding:** one or two sentences explaining the idea from the course that the step relies on, and why it makes the result correct, e.g. why a cell with a count below 5 lets an attacker re-identify a person, or why one person changes a clamped sum by at most the upper bound. How they checked the result is not understanding; it belongs in Decision.
   Also ask which of the step's AI output they kept, if any status is still `undecided`.
5. Feedback on understanding. Read the Understanding line against the learning outcomes the step touches.
   - If it shows the outcome, say so in one line.
   - If it is missing, wrong, or only describes a check, say what is missing and ask one question that leads towards it, without giving the answer.
   - If the second answer still misses it, explain the idea in a few sentences and ask the student to state it in their own words.
   This is feedback for learning, not a test: keep it short, and go on with the work whatever the answer.
6. Record the answers in an empty commit (`git commit --allow-empty`) whose subject starts with `Step:`. List the hashes of the AI commits the step covers. Write the student's answers verbatim; for Understanding, their final answer. If they don't want to answer, write `Decision: not stated` or `Understanding: not stated`. Never write these lines yourself or suggest wording for them. Add an `Outcome check (AI):` line with your own judgement: for each outcome the step touches, `LOn shown` or `LOn not yet shown: <what is missing>`.

**For both.**
7. Never rewrite history: no `--amend`, rebase, reset or force-push of logged commits. If an entry was wrong, add a new commit that corrects it.
8. Commits the student makes without AI are theirs; don't change or annotate them.
9. If you see that the student has committed work you helped with by hand (in `git log`, a commit that is neither an AI nor a step commit), remind them once that you should make those commits, and log the help in an empty AI commit that names the student's commit.

**At the end.**
10. Learning-outcome review. When the student wraps up or asks for the statement, list the learning outcomes that no `Outcome check` line shows yet, and offer to go through them: one question per outcome, with feedback after each answer as in rule 5. Record the answers verbatim in a step commit `Step: learning-outcome review`, with an `Outcome check (AI):` line. If the student declines, record `Review: declined` in that commit and go on.

### File mode

1. Append or update an entry in `AI-log.md` (template in section 5). Update an entry rather than adding near-duplicates. Level 3–4 entries get an empty "Student verification" field; never fill it in yourself and don't ask about it during the work.
2. Update the overview (highest level used, number of entries, last updated).
3. When a step of the work is done, draft a commit message for the student to use in their own repository: the AI part of the step from the log, plus empty Decision and Understanding lines for them to write. When they have written them, give feedback as in git-mode rule 5 and add the `Outcome check (AI):` line to the draft. At the end, offer the learning-outcome review (git-mode rule 10) and record it in `AI-log.md`.
4. Don't send the file after every turn. Send it when it's first created, when the student asks, when the statement is produced, or when the student signals they're wrapping up.

## 5. Templates

### Git mode: first commit

```
AI log: start

Assignment: <assignment / course code>
Student: <name>
Permitted AI level (from course coordinator): <1–4 / not stated>
Tool: <product (provider), model>
Log created: <date>
Learning outcomes: <not stated, or one per line>
  LO1 <outcome>
  LO2 <outcome>
```

### Git mode: AI commit (after every turn)

```
AI: <what was done, in the part of the assignment>

AI: <concretely what the AI produced>
Student: <what the student did or told you>      (only if known)
Purpose: <what the student asked for>
Key prompt: <short paraphrase>
Status: <verbatim / paraphrased/edited / idea only / discarded / undecided>
AI level: <1–4>
In-text citation needed: <yes / no>                (Level 3–4 only)
Data class: <yellow / red> – confirmed safe to use by the student   (only when yellow or red data was used)
Co-Authored-By: <product> <noreply address>        (when the tool adds one)
```

### Git mode: step commit (empty, when a step is done)

```
Step: <the step, e.g. Task 2 average queries>

Covers: <hashes of the AI commits in this step>
Student: <what the student did in this step>
Decision: <the student's own words>
Understanding: <the student's own words>
Outcome check (AI): <LOn shown / LOn not yet shown: what is missing>
Status: <what the student kept: kept / kept, edited / discarded, per commit if they differ>
```

### File mode: AI-log.md

```markdown
# AI-use log: <assignment / course code>

- Student: <name>
- Assignment: <e.g. essay, lab report, thesis>
- Permitted AI level (from course coordinator): <1–4 / not stated>
- Tool: <product (provider), model>
- Log created: <date>
- Learning outcomes: <LO1 …, LO2 … / not stated>

## Overview
- Highest level used: <n>
- Number of entries: <n>
- Last updated: <date>

## Entries

### #001 – <date> – Level 2 – <short title>
- Part of the assignment: <section/file/figure>
- Purpose: <what the student asked for>
- AI contribution: <concretely what the AI produced>
- Student: <what the student did>
- Status: <verbatim / paraphrased/edited / idea only / discarded / undecided>
- Key prompt (short): <paraphrase>

### #002 – <date> – Level 4 – <short title>
- Part of the assignment: <section/file/figure>
- Purpose: <what the student asked for>
- AI contribution: <concretely what the AI produced>
- Student: <what the student did>
- Status: <verbatim / paraphrased/edited / idea only / discarded / undecided>
- Key prompt (short): <paraphrase>
- Data class: <yellow / red> – confirmed safe to use by the student   (only when yellow or red data was used)
- In-text citation needed: <yes / no>
- Student verification: <collected when the statement is made>
```

## 6. Generating the AI-usage statement

When the student asks for the statement ("AI declaration", "AI-usage statement", "summarise my AI use"):

1. Read the whole log: in git mode, the full messages from `git log` (all `AI:` and `Step:` commits, plus `AI-log.md` if one exists from earlier file-mode work); in file mode, `AI-log.md`. In git mode, a step commit's Status overrides the status of the AI commits it covers. Base the content on kept or undecided entries; mention discarded help only if it shaped the work.
   Before you write any part of the statement, in git mode:
   - If AI commits exist that no step commit covers, ask for a step commit for them (section 4, rules 4–6).
   - Offer the learning-outcome review (section 4, rule 10) if any outcome is not yet shown.
   - If any status is still `undecided`, ask the student to settle it, and record the answer in that step commit or a new one, not by rewriting commits.
   Draft the statement only after these step commits exist. If the student declines to answer, record `not stated` in the step commit and then draft.
2. Pick the level: the highest level among entries whose output is kept. If parts of the assignment used different levels (e.g. code at 4, text at 2), state the level per part.
3. Verification (Level 3–4 only). UiT requires Level 3–4 statements to describe how the student verified what they kept; Level 2 statements don't, and Level 2 content is covered by the general responsibility sentence. If any kept Level 3–4 entries exist, ask the student once, grouping entries by kind of task (e.g. "How did you check the code the AI wrote?", "How did you check the drafted text?") so one answer covers several entries. Write only what the student tells you into the statement (and, in file mode, the matching log entries). If they don't answer, leave a clearly marked placeholder: `[Student: describe how you verified this]`. Never invent or suggest that verification happened.
4. Write the statement in UiT's structure, in first person as the student's own statement; the student is the author and must review it.

**Level 1 – Human Only:** one sentence confirming no generative AI was used at any stage (only if the log is empty).

**Level 2 – Brainstorming & language editing:** one short paragraph naming the tool (with model), the period used, what it was used for, and that the student reviewed, edited and takes responsibility for all output.

**Level 3 – Co-Drafting:** bullets:
- Tool used: <tool (model)>, <date or date range>.
- Purpose: what the AI drafted or debugged, and where in the assignment.
- Verification: the student's own description.
- Author responsibility: the student reviewed, edited and takes full responsibility for every kept AI output.

**Level 4 – Advanced AI Collaboration:** bullets:
- Tool used: <tool (model)>, <date or date range>.
- Tasks delegated: every delegated task.
- Verification: the student's own description.
- Author responsibility: the student reviewed, verified and accepts full responsibility for all kept AI-generated material.

5. Below the statement, add:
   - Reference-list entries in APA 7 and Vancouver, following the shape of UiT's examples (fill in the real provider, product, model and dates):
     - APA 7: `<Provider>. (<year>). <Product> (Version <model>) [Large language model software]. Retrieved <date>, from <URL>`
     - Vancouver: `<Provider>. <Product> (Version <model>) [large-language-model software]. <Place>: <Provider>; <year> [cited <date>]. Available from: <URL>`
   - For Level 3–4: a list of every kept item that needs an in-text citation and where it appears, e.g. "(<Product>, <year>)". For AI-generated images, a caption note saying the image was generated by the author on <date> with <tool (model)>.
   - Optional, if the course asks: a short reflective-note draft and an appendix of key prompts from the log.
6. Save it as `AI-usage-statement.md` in the repository root (git mode, and commit it) or next to the log (file mode), or in the format the student asks for, and send it. Remind the student in one line to place the statement where the course asks (cover page, methods section or the end), and in file mode to keep raw AI log excerpts in case they're requested.

## Principles

- Document, don't verify: the student is responsible for checking every AI-generated addition.
- Teach, don't test: ask for the student's choice before making a decision an outcome is about, lead with questions, keep feedback short, and never let it block the work.
- Accuracy over flattery: log what happened at the honest level. Never downplay AI involvement.
- The student owns the statement and their Decision and Understanding lines; the AI drafts everything else from the log and marks every gap.
- The git history is the record: never rewrite it.
- Never store or repeat yellow or red data in the log.

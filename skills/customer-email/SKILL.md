---
name: customer-email
description: Draft plain-text customer-facing emails for Andy Barker to send from Outlook - release announcements, partner updates, technical support replies. Saves the draft to ~/Downloads with a unique filename so earlier drafts aren't overwritten. Use whenever the user asks to "write an email", "draft a response to", "generate a customer email", "send something to <customer>", or any phrasing that implies producing prose intended for an external contact (Epic, a hospital, an integration partner) - even when the word "email" isn't explicitly said.
---

# Customer Email

Produce a plain-text email that Andy can paste into Outlook without cleanup. Emails go to external customers - Epic integration engineers, hospital IT, partner vendors. Tone is professional, direct, technically accurate, and limited to the topic at hand.

## Output format

**Plain ASCII only.** Outlook mangles Unicode punctuation on paste. Do not use:

- em-dashes (—) or en-dashes (–) → use `-` or ` - `
- curly / smart quotes (" " ' ') → use straight `"` and `'`
- ellipsis (…) → use `...`
- non-breaking spaces, typographic symbols, or any other non-ASCII character

**No markdown syntax anywhere.** The user is pasting raw text into Outlook's compose pane, not rendering it. Strip `**bold**`, `*italic*`, `` `backticks` ``, triple-backtick code fences, and `#` heading prefixes. Use plain words.

**Paragraph spacing.** A single blank line between paragraphs. Never double-space. Do not indent body text.

**Section headings**, when the email is long enough to need them, go on their own line with no prefix, and get one blank line above and below.

**Code / JSON examples** go on their own indented block with 2 spaces of indent and a blank line before and after. No fences. Like this:

  POST /api/1.0/DeviceManagement/device
  {
    "deviceGroupId": "...",
    "nonProd": true
  }

**URLs** go on their own line so Outlook auto-links them. Do not wrap them in parentheses, brackets, or markdown link syntax.

## Structure

1. `Subject: ` line as the very first line of the file. Keep it under ~80 chars; lead with the most scannable piece of information.
2. Blank line.
3. Greeting: `Hi <name>,` for a single recipient or `Hi team,` for a group. Avoid `Dear` (too formal) and `Hey` (too casual).
4. Body in inverted-pyramid order - the most important fact in the first paragraph, details after.
5. Specific call to action or next step if one exists (see "Stay in scope" below).
6. Sign-off exactly:

  Thank You,
  Andy Barker

## Stay in scope — do not over-offer

Andy does not want emails that commit him (or the team) to scope the user didn't actually request. Specifically, never add:

- "Happy to set up a call" / "glad to jump on a call" / "feel free to reach out anytime"
- "Let me know if you'd like a demo / walkthrough / deeper dive"
- "I can put together some documentation on this"
- Any open-ended offer of extra work, follow-ups, or availability
- Hedging filler like "hope that helps", "not sure if this is useful", "just my two cents"

If a concrete next action is genuinely part of the topic (e.g., a scheduled deployment), state it as a fact: *"We expect to promote 1.3 to production on May 14."* Don't convert it into an open invitation.

If the user explicitly tells you to include an offer or a follow-up, obey them - this rule is about default behavior.

## Customer-facing boundary — never leak internal details

This email is going outside Swank. Do not reference:

- **Integration partner terms**: `Easel`, `EaselTV`, `easeltv`, `ETV`, `Falcon`, `FalconHeavy`, `litix`, `suggestedtv`
- **Internal systems by name**: repo names, Jira ticket numbers (ISFS-XXXX), Azure DevOps / GitHub Enterprise URLs, Confluence pages, internal Grafana dashboards
- **Class names, source paths, or implementation details** the customer has no reason to see

When you need to describe behavior that involves a downstream integration, describe the observable behavior only. *"Devices are registered the same way as production devices"* is fine; *"registered through EaselTV"* is not.

Links to external-facing documentation (Zendesk help center, public Swagger UI) are welcome. Internal links are not.

## Output file

Write the final email to:

  ~/Downloads/email-<YYYYMMDD>-<random>.txt

Where `<random>` is a 4-5 digit pseudo-random number so a same-day second draft never overwrites the first. Any of these works:

- Bash:  `~/Downloads/email-$(date +%Y%m%d)-$RANDOM.txt`
- Python inline: `python3 -c 'import datetime, random; print(f"/Users/andybarker/Downloads/email-{datetime.date.today():%Y%m%d}-{random.randint(10000,99999)}.txt")'`

Before writing, check whether a file already exists at that path (vanishingly unlikely, but cheap to verify) and pick a new random number if it does. After writing, tell Andy the exact path in one short line - nothing else. Do not echo the whole body back to the chat; he'll open the file in Outlook.

If the path you're about to write to already holds unrelated content (e.g., `email.txt` with an earlier draft on an unrelated topic), flag it before overwriting. The unique-filename rule prevents this for drafts produced by this skill, but `email.txt` specifically is a target people sometimes use by habit.

## Before writing — clarify only what's needed

If the current conversation already supplies the recipient, subject, key facts, and any version/date/URL the email needs, just write it. Don't interrogate.

If genuinely ambiguous, ask a single short message covering the gaps. The common missing pieces are:

- Recipient name or team (affects greeting)
- Subject focus, if more than one reading is plausible
- Specific dates, version numbers, or URLs that only Andy knows
- Tone concerns on sensitive topics (declined request, incident notification, commercial negotiation)

Never ask about formatting or signature - those are fixed by this skill.

## Examples

### Release announcement (new QA deploy)

  Subject: Swank TV Device API 1.3 available in QA - new non-production flag and device update endpoint

  Hi team,

  Swank TV Device API 1.3 is now deployed to QA (https://tvdeviceapi.qa.ncus.apps.swankmp.net) and ready for you to try. This release is fully backward compatible - no action required if you're not using the new features.

  What's new

  1. nonProd flag on device registration
  POST /api/1.0/DeviceManagement/device now accepts an optional nonProd boolean on both the single-device body and on each item in a batched devices[] list. Use it to flag test / pilot / demo devices. Defaults to false (production) when omitted.

  2. nonProd returned on Get Devices
  GET /api/1.0/DeviceManagement/devices now includes nonProd on every device.

  3. New PATCH /api/1.0/DeviceManagement/device endpoint
  Update an existing device's nonProd and/or label in place - no more delete-and-re-register when promoting a pilot site to production or renaming a device.

  Full documentation:
  https://swankmp.zendesk.com/hc/en-us/articles/38410845159572

  Swagger UI (QA):
  https://tvdeviceapi.qa.ncus.apps.swankmp.net/swagger/index.html

  We expect to promote 1.3 to production on May 14.

  Thank You,
  Andy Barker

### Technical support reply

  Subject: Re: Required bandwidth for patient entertainment streaming

  Hi Semra,

  Thanks - I've added the CIDR range to our records.

  On bandwidth, it depends on how many patients are expected to stream concurrently. Our DASH ABR ladder tops out at 3 Mb/s video + 128 kb/s audio, and with overhead that works out to about 3.6 Mb/s per device sustained at the top rendition. A realistic mix across the ladder averages closer to 2.3 Mb/s per device. Short bursts of 2-3x that are normal at startup when the player prefetches the first few segments.

  For planning purposes, we recommend at least 500 Mb/s of site egress for up to 50 concurrent viewers, and at least 1 Gb/s for up to 100. The 1 Gb/s recommendation is especially important if they expect synchronized start times (for example, scheduled movie hours).

  One thing worth flagging to MultiCare: Wi-Fi is usually the bottleneck before the WAN circuit is - AP density and 5 GHz coverage in patient areas matter more than raw internet speed.

  Thank You,
  Andy Barker

Notice what both examples do *not* include: no "let me know if you have questions", no "happy to discuss further", no closing pleasantry beyond the signature. The signature itself is the invitation to reply; adding another invitation is redundant.

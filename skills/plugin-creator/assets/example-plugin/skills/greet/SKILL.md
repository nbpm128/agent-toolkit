---
name: greet
description: Greet a person by name in a chosen tone. Use when the user asks to write a greeting, welcome message, or short salutation and wants control over formality (formal, casual, or enthusiastic).
---

# Greet

Produce a short greeting addressed to a named person, in the requested tone.

## Steps

1. Identify the recipient's name and the desired tone. If the tone isn't given,
   default to **casual**.
2. Write a one- or two-sentence greeting matching the tone:
   - **formal** — "Dear <name>, ..."; no contractions or exclamation marks.
   - **casual** — "Hi <name>, ..."; friendly and relaxed.
   - **enthusiastic** — "<name>! ..."; upbeat, may use one exclamation mark.
3. Keep it under 40 words. Return only the greeting text, no preamble.

## Example

Input: name "Sam", tone "formal"
Output: "Dear Sam, it is a pleasure to welcome you. We look forward to working with you."

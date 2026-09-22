---
version: "1"
name: Broken Fixture
description: A deliberately broken DESIGN.md used to test the validator's error detection.
omitted: []
colors:
  secondary: "#00ff00"
components:
  bad-button:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.secondary}"
  low-contrast-label:
    backgroundColor: "#fefefe"
    textColor: "#ffffff"
---

## Overview

This fixture is intentionally broken in 7 distinct ways, one per validator rule (rule 6 fires
twice, once per undeclared missing section), so the validator's error detection can be tested
deterministically.

## Typography

Placed before Colors on purpose to trigger the section-order check.

## Colors

Defines only `secondary`, never `primary`, to trigger the missing-primary-token check.

## Colors

Repeated on purpose to trigger the duplicate-heading check.

## Elevation & Depth

Present only to keep this fixture close to realistic; carries no defect of its own.

## Components

`bad-button` references an undefined `{colors.accent}` token, and `low-contrast-label` pairs a
near-white background with a white text color to trigger the contrast check.

## Do's and Don'ts

This fixture has no `Layout` or `Shapes` heading, and neither is declared in frontmatter
`omitted:`, to trigger the missing-section check twice.

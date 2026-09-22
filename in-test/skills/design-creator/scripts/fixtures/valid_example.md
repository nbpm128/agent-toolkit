---
version: "1"
name: Fixture System
description: A minimal but complete valid DESIGN.md used to test the validator.
omitted: []
colors:
  primary: "#111111"
  on-primary: "#ffffff"
typography:
  body-md:
    fontFamily: Inter
    fontSize: 16px
rounded:
  md: 0.5rem
spacing:
  unit: 8px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
---

## Overview

A minimal reference system used only to exercise the validator against a fully compliant file.

## Colors

A near-black primary with a white on-primary text color, chosen for maximum, unambiguous contrast.

## Typography

A single body style set in Inter at 16px.

## Layout

An 8px base spacing unit governs all gaps in this fixture.

## Elevation & Depth

No elevation treatment is exercised by this fixture.

## Shapes

A single 0.5rem corner radius is used throughout.

## Components

The primary button uses the primary color as its background and on-primary as its text color,
giving it a high-contrast, unmistakably "press me" appearance.

## Do's and Don'ts

Do keep the primary/on-primary pairing for any high-emphasis action. Don't introduce a second
accent color into this fixture — it exists only to stay valid, not to look interesting.

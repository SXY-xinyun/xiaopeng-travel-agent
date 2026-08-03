# DESIGN.md

## Direction
Automotive cabin HUD: deep graphite, single electric teal accent, amber for judge/alert signals only.

## Type
- Display: Space Grotesk
- Body: Noto Sans SC
- Data: JetBrains Mono (tabular numerals)

## Color
- Background: `#0a0e12` → `#121820`
- Text: `#e8f0ed` / muted `#7f958f`
- Accent: `#3ecfb0`
- Signal/warn: `#d4a84b`
- Danger: `#e86a6a`

## Layout
Three-column product shell (scenarios · cockpit · insight), max-width 1440px. Dense but readable. Cards only where interaction needs a container; insight uses hairline dividers.

## Motion
Staggered panel rise, map road scroll + car nudge, bubble fade-in. Respect `prefers-reduced-motion`.

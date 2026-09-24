---
name: spendly-frontend
description: Build new pages, components, and UI features for the Spendly expense tracker (Flask + Jinja2 templates + hand-written CSS + vanilla JS) so they look and behave exactly like the existing app. Use this skill whenever the user asks to create or change anything visual in Spendly — a new page (profile, add/edit expense, settings), a form, a card, a table or list, a modal, a chart, empty states, flash messages, responsive fixes, or small JS interactions — even if they just say "make the add expense page" or "add a UI for X" without mentioning design. Also use it for any Flask/Jinja/vanilla-CSS(repo:https://github.com/MayurNandanwar/Spendly) project that should follow the same warm, editorial "paper and ink" design language.
---

# Spendly Frontend

Spendly is a personal expense tracker. Its frontend is deliberately simple: server-rendered Jinja2 templates, one global stylesheet with design tokens, one CSS file per page area, and a small amount of vanilla JS. No frameworks, no build step, no npm. New UI should feel like it was written by the same person who wrote the existing pages — same tokens, same class naming, same spacing rhythm, same restraint.

Before writing anything, look at what already exists (`templates/`, `static/css/style.css`, `static/css/dashboard.css`, `static/js/main.js`). Reuse existing classes when they fit; only add new ones when the component is genuinely new.

For the full catalog of existing components with copy-ready markup and CSS, read `references/components.md`.

## Stack rules (and why)

- **Every page extends `base.html`.** It provides the navbar, flash messages, footer, fonts, and `style.css`. Put page content in `{% block content %}`, page CSS links in `{% block head %}`, page scripts in `{% block scripts %}`, and set `{% block title %}` as `Page name — Spendly` (em dash).
- **Every internal link and form action uses `url_for()`.** Hardcoded paths break when routes change. This includes `action=` on forms and `static` files.
- **Page-specific styles go in a new file** `static/css/<area>.css`, linked from that template's `head` block. Global/reusable pieces (buttons, form inputs, cards used on many pages) go in `style.css`. Never add `<style>` blocks or `style="..."` attributes — the one exception is data-driven values Jinja computes, like a bar width `style="width: {{ pct }}%"`.
- **Vanilla JS only.** No React, jQuery, Alpine, chart libraries, or CDN scripts. Shared behavior goes in `static/js/main.js`; page-only behavior can go in `static/js/<area>.js` loaded through `{% block scripts %}`. Match the existing style: `document.addEventListener("DOMContentLoaded", function () { ... })`, `var`, `function` expressions, and `data-*` attributes as hooks (e.g. `data-auto-dismiss="true"`) rather than styling classes.
- **Server-rendered first.** Filters, forms, and navigation work through plain GET/POST forms (see the dashboard filter bar, which uses `<button type="submit" name="range" value="...">` chips). Use JS only to enhance, not to replace working HTML.
- **Only touch routes the task targets.** If a page needs a route, it goes in `app.py`; data access goes in `database/db.py`. Don't implement unrelated placeholder routes.

## Design language

The look is warm, calm, and editorial: off-white "paper", near-black "ink", a deep forest-green accent, and a serif display font for headings and money. Keep it quiet — thin borders instead of heavy shadows, generous whitespace, very little color.

**Always use the tokens from `:root` in `style.css`; never introduce raw hex values** (the four chart bar colors are the only existing exception).

| Purpose | Token |
|---|---|
| Page background | `--paper` (`#f7f6f3`) |
| Alternate section band | `--paper-warm` |
| Cards, inputs on cards | `--paper-card` (white) |
| Main text / primary buttons | `--ink` |
| Labels, secondary text | `--ink-soft`, `--ink-muted` |
| Placeholders, dates, faint meta | `--ink-faint` |
| Brand accent (links, focus, hover, success) | `--accent` + `--accent-light` |
| Secondary accent (amber) | `--accent-2` + `--accent-2-light` |
| Errors / destructive | `--danger` + `--danger-light` |
| Borders | `--border` (outer), `--border-soft` (inner dividers) |
| Radii | `--radius-sm` 6px (buttons, inputs, rows), `--radius-md` 12px (cards), `--radius-lg` 20px (featured cards), `999px` (pills, chips, bar tracks) |

**Typography**
- `--font-display` (DM Serif Display) for page titles, section titles, card titles, and **all money amounts**. Titles use sizes like `2rem`–`2.25rem` for page H1, `clamp()` for hero/CTA.
- `--font-body` (DM Sans) for everything else. Body text is `0.85rem`–`1rem`; buttons and nav `0.9rem`, weight 500.
- Small caption labels (e.g. "TOTAL SPENT", "FROM"): `0.75rem`–`0.8rem`, weight 500, `text-transform: uppercase`, `letter-spacing: 0.05em–0.08em`, color `--ink-muted` (or `--accent` inside accent cards).
- An `<em>` inside a display heading becomes italic accent green — use sparingly for emphasis.

**Surfaces and interaction**
- Standard card: `background: var(--paper-card); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.5rem–2rem;`
- Featured card (one per view, e.g. a chart): `--radius-lg` plus `box-shadow: 0 8px 40px rgba(0,0,0,0.06)`. No other shadows anywhere.
- Highlight card (key number): `--accent-light` background with `1px solid var(--accent)` border.
- Empty state: card with `1px dashed var(--border)`, centered muted text.
- Hover pattern: dark things turn `--accent` (`.btn-primary`, `.btn-submit`, `.nav-cta`); outlined things get an `--ink` border and text (`.btn-ghost`, `.filter-chip`). Focus on inputs: `border-color: var(--accent)`, `outline: none`.
- Transitions are `0.2s` on color/background/border; bar widths animate at `0.6s ease`.
- Icons are Unicode glyphs in the accent color (`◈ ₹ ◎ ◷`), not icon fonts or SVG libraries.

**Content conventions**
- Currency is Indian Rupees: `₹{{ "%.2f"|format(amount) }}`. Example names and data are Indian (e.g. placeholder `Nitish Kumar`, `nitish@example.com`).
- Copy is short, friendly, sentence case: "Welcome back", "Create one free", "No expenses found for this period."

## Layout and naming

**Section pattern.** Every page area is a `<section class="<area>-section">` with horizontal padding `2rem`, wrapping a `<div class="<area>-inner">` with `max-width: var(--max-width); margin: 0 auto;`. Narrow form pages use `--auth-width` (440px) instead, like `.auth-container`.

**Class names** are kebab-case, flat, and prefixed by the component: `.expense-row`, `.expense-main`, `.expense-amount`; `.filter-bar`, `.filter-chip`, `.filter-field`. No BEM `__`/`--`, no utility classes. States use an `is-` prefix: `.is-active`, `.is-invalid`. Variants use a numeric or descriptive suffix class alongside the base (`.category-bar category-bar-1`).

**CSS file structure.** Group rules under the existing banner comment style, and put media queries in a final "Responsive" section:

```css
/* ------------------------------------------------------------------ */
/* Section name                                                        */
/* ------------------------------------------------------------------ */
```

4-space indentation; tiny single-declaration rules may sit on one line (`.form-group { margin-bottom: 1.25rem; }`).

**Responsive.** Desktop-first with `max-width` queries at `900px` (grids/columns collapse to one column, secondary visuals may hide), `700px` (horizontal rows stack), and `600px` (tighter padding, nav trims). Use flexbox/grid with `flex-wrap` and `gap`; use `min-width: 0` on flex children that hold text.

## Forms

Forms are the most common new UI in Spendly. Mirror `register.html`:

- Wrap in `.auth-card` (or a normal card) with `<form method="POST" action="{{ url_for('...') }}">`.
- Each field: `.form-group` > `<label for>` + `<input class="form-input">`. Add `is-invalid` to the input and a `<p class="field-error">` below when `errors.<field>` exists.
- Re-fill values on error with `value="{{ field }}"` (never re-fill passwords).
- Form-level errors use `.auth-error`; post-redirect success uses `flash(..., "success")`, which `base.html` renders as `.flash flash-success`. If you need a new flash category, add a matching `.flash-<category>` rule using the token pairs (e.g. `--danger-light`/`--danger`).
- Full-width submit is `.btn-submit`; inline actions use `.btn-primary` / `.btn-ghost`.
- Use proper input types (`email`, `date`, `number` with `step="0.01" min="0"` for amounts, `<select class="form-input">` for category) plus `required`, `autofocus` on the first field.

## Known inconsistencies — don't copy these

The existing code has a few slips. When you touch these files, you may fix them; never replicate them in new code:
- `login.html` uses a hardcoded `action="/login"` — should be `url_for('login')`.
- The logout form in `base.html` has `style="display: inline;"` — should be a class.
- `landing.html` renders `.category-breakdown` / `.category-pill`, which have no CSS; `dashboard.css` defines the styled `.category-card` / `.category-bar-row` component instead. Use the `.category-card` version for category breakdowns.

## Before you finish

Check the result against this list:
1. Template extends `base.html`, sets a title, and links its own CSS in `head` if it has one.
2. No hardcoded URLs, no inline `<style>`, no raw hex colors, no new libraries.
3. All sizes/colors/radii come from tokens; money uses the display font and `₹` with two decimals.
4. There's an empty state for any list, and error states for any form.
5. It still looks right at 900px and 600px widths.
6. Mention to the user any new files created and any route/db work that's still needed.
---
name: make-revealjs-presentation
description: >-
  Create or update a RevealJS HTML presentation using the repository's bundled slide template.
  USE FOR: create RevealJS talks, make HTML slide decks, build presentation slides, start a new conference talk deck, convert a talk outline into RevealJS slides.
argument-hint: <output_html_path>
---

# Make a RevealJS presentation

Use this skill when the user wants a RevealJS-based slide deck or wants to start a new talk from the repository's house template.

## Default approach

Start from the bundled template asset instead of rebuilding the RevealJS shell from scratch:

- Template asset: `./assets/index.html`
- Copy that file to the requested output path, then edit the copied file.
- Keep the RevealJS CDN includes and `Reveal.initialize(...)` block unless the user explicitly asks to change them.

## What to customize first

After copying the template, replace these placeholders before expanding the deck:

- `Talk Title`
- `Conference Name · Month Year`
- `Your Name`
- `Role · Company · website.example`
- Example links like `filename.html` and `example.com/...`

Then rewrite or remove the example slides so the deck matches the user's topic.

## Template conventions

- The template is intentionally simple and close to stock RevealJS.
- Section divider slides use `class="heading-only"`.
- Code slides are just normal sections with a `<pre><code>` block.
- If a code badge or copy-button plugin is in use and should be suppressed for one slide, add `class="no-code-badge"` to that section.

## Customization tips

### Body font

Change the body font in the `.reveal` rule near the top of the template:

```css
.reveal {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

Examples:

- Minimal/system default: keep the existing stack
- Sans-serif web font: `font-family: 'Work Sans', sans-serif;`
- Serif deck: `font-family: 'Source Serif 4', serif;`

If using a web font, also add the corresponding `<link rel="stylesheet">` in `<head>`.

### Heading font

Change headings separately in:

```css
.reveal h1,
.reveal h2,
.reveal h3 {
  font-family: inherit;
}
```

Examples:

- Match body text: keep `inherit`
- Distinct headings: `font-family: 'Roboto', sans-serif;`
- Editorial style: `font-family: 'Fraunces', serif;`

### Text sizing

Adjust the default body sizing here:

```css
.reveal p,
.reveal li,
.reveal td,
.reveal th {
  font-size: 1em;
}
```

Increase or decrease that `font-size` when the user wants a generally larger or smaller deck.

### Code block styling

Global code block styling lives in:

```css
.reveal pre { ... }
.reveal pre code { ... }
```

Adjust those rules for larger code, different padding, or lighter/heavier borders.

### Divider slides

The divider slide look is controlled by `section.heading-only` and the underline rule:

```css
.reveal section.heading-only h1::after,
.reveal section.heading-only h2::after,
.reveal section.heading-only h3::after { ... }
```

Remove that block if the user wants divider slides to look more like plain RevealJS headings.

### Color contrast

If the user customizes colors, keep text/background combinations at accessible contrast.

- Prefer dark text on a light background or light text on a dark background.
- Be especially careful with body text, slide numbers, links, and code blocks.
- Recheck contrast after changing theme colors, background fills, or heading styles.

## Accessibility

Preserve accessibility basics when creating or customizing decks.

- Keep text/background contrast accessible, especially after theme changes.
- Make sure links have discernible text.
- Make sure images have alt text if they convey meaning.
- Treat plugin-generated UI separately from slide content when reviewing issues. `RevealMenu` currently has a known accessibility issue: its generated menu trigger may lack a discernible accessible name. If the user keeps the plugin, note that this can remain as an axe violation even when the slide content itself is fine.

### Example axe-core audit

If the user asks for an accessibility review in VS Code, open the deck in the integrated browser and run axe-core on the rendered page.

Example Playwright snippet:

```js
await page.addScriptTag({
  url: 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js'
});

const results = await page.evaluate(async () => {
  return await window.axe.run(document, {
    runOnly: {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa']
    }
  });
});
```

When reporting results:

- Separate actual `violations` from `incomplete` checks.
- Call out the exact HTML or selector for each real issue.
- Distinguish between deck-author issues and plugin-generated issues.
- If contrast checks are inconclusive because Reveal overlays or transforms confuse axe, say that clearly instead of reporting them as confirmed failures.

## Editing guidance

- Prefer plain sections, headings, lists, tables, images, and code blocks over custom layout systems.
- Do not add extra decorative CSS unless the user asks for a stronger visual style.
- Keep the deck black-on-white by default unless the user wants a themed presentation.

## Validation

After creating or editing the deck:

1. Validate the HTML file for diagnostics.
2. Open it in the integrated browser.
3. If the user asks for accessibility review, run an axe audit on the rendered page and report actual violations separately from inconclusive checks.
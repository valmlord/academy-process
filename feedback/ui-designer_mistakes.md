# ui-designer mistakes

Seeded with design-discipline rules; append real lessons as they are found. Load before working.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### Seeded: shadcn defaults copied without computing contrast

The shadcn light defaults for `--ring` and `--input` measure 2.584:1 and 1.260:1 on white, below the
3:1 that WCAG 1.4.11 requires for focus rings and control boundaries.
Rule: Re-measure every default you keep with `scripts/design_tokens.py`; never assume a library default
passes.

### Seeded: A token defined in `:root` only

A colour token missing from `.dark` falls back to its light value in dark mode, where its contrast was
never checked.
Rule: Every colour token is defined in both `:root` and `.dark`.

### Seeded: A radius step or font stack defined only in `@theme inline`

Browsers drop `@theme inline` as an unknown at-rule, so a prototype using `var(--radius-sm)` from there
renders without it.
Rule: Declare every variable a prototype needs in the `:root` block of `proto.css`, with exactly the
`@theme inline` value where the name exists there.

### Seeded: shadcn's stock destructive tokens are outside sRGB

The shadcn defaults `--destructive: oklch(0.577 0.245 27.325)` (light) and `oklch(0.704 0.191 22.216)`
(dark) lie outside the sRGB gamut, so browsers gamut-map them differently and the validator rejects them
as "out of sRGB gamut".
Rule: Pick in-gamut destructive values and measure them with `python3 -I scripts/design_tokens.py pair`
against every surface they sit on, in both themes.

### 2026-10-29: Gallery markup that differs from the pages it documents (#50)
The gallery's left-pane Tabs demo is labelled "Урок" while the lesson page uses "Разделы урока"; its top bar
has an `aria-haspopup="menu"` trigger with no menu, no `data-menu-trigger` and no `data-region`; its warning
Alert carries a description ("Урок можно читать и сейчас.") that is in no copy set and no page. Dev treats the
gallery as the component reference and copies these.
Rule: Diff each gallery composition against the page markup (classes, roles, accessible names) before
handing over; gallery copy is either register copy or obviously placeholder text.

### 2026-10-29: Menu item focus drawn only as a 1.09:1 background (#50, judge_ux round 1)
`proto.css` `.dropdown-item:focus-visible { background: var(--accent); outline: none; }` copies shadcn's
`focus:bg-accent outline-hidden`. `accent` on `popover` measures 1.090:1 light and 1.185:1 dark, so the item
focused with the arrow keys in "Действия" and the user menu is practically invisible (WCAG 2.4.7, 1.4.11).
Rule: Every element that removes the outline keeps a focus indicator measured at 3:1 against its adjacent
colours with a `pair` run; a background change alone counts only if that pair passes.

### 2026-10-29: Environment pane overflows onto the check bar in one-pane mode (#50, judge_ux round 1)
`.pane[data-pane="environment"]` has no overflow handling while `.terminal-frame` / `.terminal-placeholder`
keep `min-height: 12rem`; in one-pane mode at heights above the 30rem document-mode breakpoint (375x667,
320x500) the pane's content paints over the check bar row, and a focused "Проверить" is entirely covered
(WCAG 2.4.11, 1.4.10). The lesson pane was safe only because its body is a `.scroll-area`.
Rule: Every grid cell of a fixed-height layout either scrolls (`overflow: auto`) or provably fits; test
mid heights between the breakpoints, not only 320x200 and 1280x800.

### 2026-10-29: The gallery kept a second "Чему научитесь" markup after `.outcomes` (#50, judge_ux round 3)
The Collapsible section of `components.html` still draws outcomes as `div.stack > h4.text-sm + ul.text-sm`
without `.outcomes`, so its lists take the UA indent (40px) and 14px margins, off the spacing scale, while
the new `.outcomes` entry and both pages use `space-6` and no margin. The gallery is dev's reference: it now
shows two structures for one component.
Rule: When a component is promoted, replace every gallery example of the same content with the promoted
markup and grep the gallery for the old one.

### 2026-10-29: proto.js reached CI unformatted (#50)

`design/system/proto.js` is inside biome's scope (`biome.json` includes `**/*.js`), and nobody on the design team ran
biome before reporting, so PR #67 went red on `pnpm lint` and the pipeline had to be re-opened for a format pass.
Rule: run `node_modules/.bin/biome check design/` before reporting any change to a `.js` or `.json` file under
`design/`; it must report no error.

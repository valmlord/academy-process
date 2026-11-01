# Design contract (summary for design agents)

The authoritative definition is ADR-0006 (`docs/adr/0006-design-dev-contract.md`). The validator
`python3 -I scripts/design_tokens.py check design` enforces the machine-checkable part. Summary:

```
design/README.md                     purpose, how to open prototypes, page table (slug, status, link)
design/flows/ia.md                   sitemap, navigation, page inventory, flow registry (F<n> -> file -> title)
design/flows/<journey>.md            flows "## F<n>: <title>", steps "1. F<n>.<m> ..." (ids unique across files)
design/system/tokens.css             THE token file: @custom-variant dark, :root, .dark, @theme inline; nothing else
design/system/README.md              type, spacing, radius, motion scales; component inventory; dark-mode rules
design/system/proto.css              prototype only: a :root block of prototype variables, then component styles
design/system/proto.js               prototype only behaviour (theme toggle, states, dialogs)
design/system/components.html        every inventory component, both themes
design/pages/<slug>/prototype.html   no build step; links ../../system/{tokens.css,proto.css,proto.js}
design/pages/<slug>/acceptance.md    acceptance notes with the fixed headings below
```

- Token values in `:root`/`.dark`: a colour (`oklch(...)` or hex) or a length, number, `calc()` or `var()`.
  Every shadcn colour token exists in both themes and is mapped as `--color-<name>: var(--<name>)`.
- A prototype may use `var(--x)` only for names declared in `tokens.css` `:root`/`.dark` or as `--x:` in
  a prototype file. `@theme inline` names are invisible to browsers: alias them in `proto.css` `:root`
  with exactly the `@theme inline` value. A prototype never redeclares a `tokens.css` name.
- Prototypes: `<html lang="ru">`, viewport meta, Russian `<title>`, follow `prefers-color-scheme`, states
  `[data-state="<name>"]` opened by `#state-<name>`, `data-step="F<n>.<m>"` on the element of each flow
  step, relative links only, no absolute or protocol-relative URL anywhere except an `<a href>` value.
- Acceptance notes headings: Route; Prototype; Flows; Status; Purpose; Layout and breakpoints; Components;
  States; Interactions and keyboard; Copy; Accessibility notes; Acceptance checks (`AC1..`); Open questions.
- `Status: draft | ready`, written only by the product-designer. `ready` binds dev only on `main`.
- English except prototype UI copy and the Copy table: Russian, straight quotes, no em dashes.

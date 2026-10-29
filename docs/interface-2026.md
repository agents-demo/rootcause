# Interface 2026 — design brief

**The goal.** Make RootCause feel like a 2026 instrument for quality decisions, not a 2019 admin
dashboard with a dark theme. The stage piece can stay theatrical. The daily tool must become calmer,
faster, more legible and more confident.

**The sentence.** *An industrial instrument panel with editorial calm: type-led, box-light,
command-first, evidence-first — and AI that is ambient, cited and never in charge.*

---

## What “2026” means here

2026 is not neon, glass and 3D. The visual language that feels current in serious software is:

- **Calm surfaces, dense on demand.** The default screen is quiet; detail appears when asked for.
- **Typography leads.** Hierarchy comes from scale, weight and space, not from another rounded card.
- **One accent, semantic color.** Colour means state: evidence, risk, approved — not decoration.
- **Spatial layout.** Asymmetric canvases, rails and docks replace grids of equal cards.
- **Command-first.** `⌘K`, natural language, direct navigation and actions without hunting menus.
- **Explainable motion.** Animation shows a signal becoming a watch, a cause being rejected, a
  recommendation being approved. It is not ambient decoration.
- **AI as infrastructure.** No chatbot bubble. The agent is a status line, a suggestion, a citation,
  a command. It never becomes the interface.
- **Accessible and fast by default.** WCAG 2.2 AA, keyboard-complete, reduced motion, 200% zoom,
  Core Web Vitals budgets, low-end hardware.
- **Adaptive by role and device.** Operator, engineer, quality manager and admin do not need the same
  home screen. Mobile is a first-class triage surface, not a squeezed desktop.

## What we are moving away from

These are the current tells that make the product read as 2019–2022:

| Tell | Why it ages | Replace with |
|---|---|---|
| Fixed 238 px sidebar + top bar | Admin-template shell | Instrument bar + context rail + command palette |
| KPI card grid | Equal-weight boxes flatten priority | One operational header + decision queue |
| 8–9 px uppercase labels | Dated dashboard microtype; hurts readability | 11–12 px labels, 14–16 px body, real type scale |
| Everything in a rounded panel | Chrome competes with evidence | Section rules, tonal surfaces, fewer boxes |
| Amber + cyan + red + purple decoration | Visual noise | One accent + semantic risk/approval colours |
| Radial glows and glass blur | 2020–2022 devtool aesthetic | Precise gradients only where they explain depth |
| Tables as the default answer | Dense but undifferentiated | Board/queue/table modes, inline preview, bulk actions |
| Charts in cards with legends | Chartjunk | Direct labels, annotations, small multiples, linked evidence |
| Reveal/fade motion only | Decoration, not explanation | State-transition grammar and shared elements |
| Chat as the AI surface | 2023 chatbot reflex | Command palette, inline citations, ambient agent status |

## Design principles

1. **Evidence before decoration.** If an element does not carry a fact, a state or a decision, it
   does not get visual weight.
2. **Type first, boxes second.** Use type scale, spacing and rules. A panel is a last resort, not the
   default container.
3. **One primary action per surface.** The eye should know what to do in under two seconds.
4. **Calm until needed.** Dense data on demand; not dense everywhere.
5. **Explain the state change.** Motion must teach the relationship: signal → watch → case →
   containment → report.
6. **The engineer is the interface.** AI proposes, cites and waits. Never a magic answer.
7. **Accessible is the aesthetic.** Large enough type, contrast, focus, keyboard and reduced motion
   are part of the visual language.
8. **Stage and desk are different products.** The stage is theatre; the desk is a daily instrument.
   Do not force one skin onto both.

## Target archetype

> **Industrial instrument panel × editorial investigation desk.**

- **Instrument panel:** live status, precise numbers, direct labels, a quiet grid, no ornament.
- **Editorial desk:** a case reads like a document with evidence in the margin, not a form in a card.
- **Decision queue:** the home screen is “what needs me now,” not “here are eight charts.”

### Signature moves

1. **The instrument bar.** Site, line, live status, command/search, alerts and user in one thin bar.
2. **The decision queue.** Home is a ranked list of decisions: watch, case, report, action.
3. **The evidence canvas.** A case is a spatial canvas: part image, findings, timeline and evidence
   pinned to the fact they support.
4. **The decision dock.** A persistent, calm strip at the bottom of a case/review: accept, reject,
   add, sign — with the consequence stated.
5. **The command palette.** Navigate, search, run a scan, ask a case, open a report, stop the
   scheduler.
6. **Quiet AI.** Agent activity is a status line and inline suggestions with citations, not a chat.
7. **Explainable transitions.** Rejecting a cause visibly re-weights the stack; a signal visibly
   becomes a watch; a recommendation moves to approved.
8. **Desk mode.** A light, high-contrast daily theme alongside the dark control-room theme.
9. **Density switch.** Comfortable vs compact, remembered per user.
10. **No 8 px type.** Ever. The smallest label is 11 px with safe contrast.

---

## Phase 6 plan

### 6.0 Baseline, direction and evidence

- [ ] Capture a visual baseline of every route at 1440, 1024, 768 and 390 px **(S)**
- [ ] Inventory every component, page, CSS class and one-off pattern; flag duplicates **(M)**
- [ ] Record current task metrics: time to first decision, time to find evidence, report sign-off time **(M)**
- [ ] Recruit 5 engineers/quality managers for task-based testing before redesign **(S)**
- [ ] Audit the current UI against the 2019 tells table; agree what must go **(S)**
- [ ] Choose the 2026 direction with the team: instrument panel × editorial desk **(S)**
- [ ] Write and sign the design principles and non-goals **(S)**
- [ ] Define success metrics and kill criteria before visual work starts **(S)**
- [ ] Protect the stage piece as an explicit exception to the daily design system **(S)**
- [ ] Decide light “desk” mode scope and dark “control room” scope **(S)**

### 6.1 Foundations: tokens, type and colour

- [ ] Design tokens: surface levels, text roles, borders, radii, elevation, spacing, z-index **(M)**
- [ ] Type scale: 11/12/13/14/16/20/24/32/44 with weights and line heights **(M)**
- [ ] Replace all 8–9 px type; minimum label 11 px and body 14 px **(S)**
- [ ] Variable font selection and subsetting; system fallback with matched metrics **(M)**
- [ ] Semantic colour roles: evidence, risk, approved, rejected, neutral, disabled **(M)**
- [ ] One primary accent; remove cyan/amber/red/purple competition **(S)**
- [ ] Dark and light palettes with measured WCAG contrast for every role **(M)**
- [ ] Colour-blind simulation for risk, approved and chart series **(S)**
- [ ] Spacing scale on a 4 px base; no arbitrary margins **(S)**
- [ ] Radius scale: 4/6/10 only; no 18–22 px pill panels **(S)**
- [ ] Elevation: two levels maximum; prefer tonal surfaces and rules **(S)**
- [ ] Density tokens: comfortable and compact, persisted per user **(M)**
- [ ] Motion tokens: durations 120/180/240 ms, easing curves, reduced-motion fallbacks **(S)**
- [ ] Icon set audit: one stroke weight, 16/20 px, optical alignment **(S)**
- [ ] Focus ring system: visible on every interactive element, no outline removal **(S)**
- [ ] Design-system documentation site with live examples and do/don’t **(M)**
- [ ] CSS architecture: layers, tokens, utilities, component boundaries, no global leaks **(M)**
- [ ] Deprecation list for the old card/chip/meter classes **(S)**

### 6.2 Shell and information architecture

- [ ] Replace the fixed sidebar/top bar with a thin instrument bar **(L)**
- [ ] Add a 64 px mode rail with labelled hover/focus states **(M)**
- [ ] Add a contextual right rail for evidence, ask and activity **(M)**
- [ ] Build a command palette with navigation, search, actions and ask **(L)**
- [ ] Add global search across cases, watches, batches, evidence IDs and reports **(M)**
- [ ] Define role homes: operator, engineer, quality manager, admin **(M)**
- [ ] Make the home screen a decision queue, not a KPI card grid **(L)**
- [ ] Add a persistent decision dock for case, watch and report surfaces **(M)**
- [ ] Make every pane addressable by URL and restorable on reload **(M)**
- [ ] Add recent, pinned and “continue where you left off” **(S)**
- [ ] Add keyboard map: `⌘K`, `g` navigation, `j/k` queue, `a/r` decision, `?` help **(M)**
- [ ] Add a focus mode for review and report sign-off **(S)**
- [ ] Replace modals with sheets or inline panels except for destructive confirmation **(M)**
- [ ] Add a notification sheet and alert triage from anywhere **(S)**
- [ ] Mobile: bottom bar, sheets, thumb-first triage, no desktop squeeze **(M)**
- [ ] Tablet: split view with queue + detail **(S)**
- [ ] Remove dead navigation and one-off route titles **(S)**

### 6.3 Core surfaces

- [ ] Redesign Home as “what needs a decision now”: top risk, open cases, actions due, coverage **(L)**
- [ ] Redesign Watchlist as a risk board with grouping, inline preview and bulk triage **(L)**
- [ ] Redesign Watch detail as a signal story: why now → checks → containment → outcome **(L)**
- [ ] Redesign Case workspace as an evidence canvas with pinned findings **(L)**
- [ ] Add a cause stack that re-weights visibly on accept/reject **(M)**
- [ ] Add side-by-side case/evidence compare **(M)**
- [ ] Redesign Review as a decision queue with keyboard-first triage **(M)**
- [ ] Redesign Reports as a document with evidence in the margin and inline sign-off **(L)**
- [ ] Redesign Dashboard as a narrative of small multiples, not a card wall **(M)**
- [ ] Redesign Alerts as an inbox with grouping, snooze and one-key triage **(M)**
- [ ] Redesign Shift brief as an editorial one-pager, print-first **(M)**
- [ ] Redesign Connectors/Admin as status-led settings, not forms in panels **(M)**
- [ ] Redesign Mobile capture as a two-tap flow with a clear next action **(M)**
- [ ] Add empty, loading, error and offline states to every surface **(M)**
- [ ] Add onboarding that teaches by doing, not a tour overlay **(S)**

### 6.4 Data visualization

- [ ] Build one chart primitive set with consistent scales, padding and typography **(L)**
- [ ] Direct labels and annotations; remove legends where the label can sit on the series **(M)**
- [ ] Small multiples for line and sensor comparison; no dual-axis charts **(M)**
- [ ] Show uncertainty, spec limits and the defect window explicitly **(M)**
- [ ] Linked highlighting: chart point ↔ evidence ↔ table row ↔ image finding **(L)**
- [ ] Accessible chart fallback: data table and text summary for every chart **(M)**
- [ ] Colour-blind-safe series palette and patterns where needed **(S)**
- [ ] Real-time updates without layout shift; stable axes and transitions **(M)**
- [ ] Sparkline strip for context instead of another card **(S)**
- [ ] Remove decorative donuts, gauges and gradients that do not encode data **(S)**

### 6.5 Motion and state transitions

- [ ] Define the transition grammar: signal → watch → case → containment → report **(M)**
- [ ] Use shared-element transitions for a case opening from a queue **(M)**
- [ ] Animate ranking re-weight after a reject, with a clear before/after **(M)**
- [ ] Animate recommendation approval as a state change, not confetti **(S)**
- [ ] Add route-level view transitions with a graceful fallback **(M)**
- [ ] Respect `prefers-reduced-motion` everywhere; no essential meaning in motion **(S)**
- [ ] Keep interactions under 240 ms and 60 fps; measure long tasks **(S)**
- [ ] Remove ambient animation that does not explain state **(S)**

### 6.6 AI-native interaction

- [ ] Add “Ask this case” with answers restricted to case evidence and explicit citations **(L)**
- [ ] Add “Ask the watch” for why-now, what-to-check and what-would-falsify **(M)**
- [ ] Command palette understands natural language: “hold batch B-2291” opens the recommendation **(L)**
- [ ] Every generated sentence carries source IDs and model version **(M)**
- [ ] Show a clear “no answer without evidence” state **(S)**
- [ ] Inline suggested checks and causes with accept/reject, never auto-apply **(M)**
- [ ] Ambient agent status: working, waiting, evidence gathered, needs a human **(S)**
- [ ] Latency skeletons, cancel and retry for every AI action **(S)**
- [ ] Offline degradation message that says what still works **(S)**
- [ ] AI eval harness for answer faithfulness, citation coverage and refusal **(M)**
- [ ] No chatbot-first surface, no avatar, no typing animation **(S)**
- [ ] Role-aware language: operator, engineer, manager **(S)**

### 6.7 Accessibility, content and trust

- [ ] WCAG 2.2 AA audit across every route; fix all critical issues **(L)**
- [ ] Keyboard-only completion of the five core tasks **(M)**
- [ ] Screen-reader pass with NVDA and VoiceOver on queue, case and report **(M)**
- [ ] 200% zoom and 320 px reflow without loss of function **(M)**
- [ ] Target size ≥ 44 px on touch; focus order and skip links **(S)**
- [ ] Charts and images have text alternatives and data tables **(M)**
- [ ] No meaning by colour alone; status always has text/icon **(S)**
- [ ] Plain-language pass: causes, evidence, confidence, containment, limitations **(M)**
- [ ] Units, time zones, dates and precision consistent everywhere **(S)**
- [ ] Error, permission, offline and “no evidence” copy reviewed **(S)**
- [ ] Trust copy: recommendation vs action, human approval, provenance **(S)**
- [ ] Localization-ready strings and RTL layout check **(M)**

### 6.8 Performance and engineering

- [ ] Performance budgets: LCP < 1.5 s, INP < 200 ms, CLS < 0.05 on the pilot laptop **(M)**
- [ ] Bundle budget and route-level code splitting **(M)**
- [ ] Font subsetting and preload; no external font calls **(S)**
- [ ] SVG optimisation and image lazy-loading with reserved space **(S)**
- [ ] Virtualise long case/watch tables; keep scroll at 60 fps **(M)**
- [ ] Optimistic updates with rollback for decisions **(M)**
- [ ] Service-worker versioning and safe cache invalidation **(S)**
- [ ] Low-end device and 4-year-old laptop test **(M)**
- [ ] No layout shift from live data; reserve chart and number space **(S)**
- [ ] Remove unused CSS and old design-system classes **(M)**
- [ ] Storybook or equivalent living component catalogue **(M)**
- [ ] Visual regression snapshots for every core surface **(M)**
- [ ] Axe/Lighthouse checks in CI with budgets, not just reports **(M)**
- [ ] Feature flags for page-by-page rollout **(M)**

### 6.9 Validation and rollout

- [ ] Five-user task test: find top risk, reject a cause, approve containment, sign report **(M)**
- [ ] Measure time-to-first-decision before/after; target −30% **(M)**
- [ ] SUS ≥ 80 with the pilot group **(M)**
- [ ] Command-palette adoption ≥ 70% of weekly active engineers **(S)**
- [ ] Mobile triage success ≥ 80% one-handed **(M)**
- [ ] Accessibility sign-off: WCAG 2.2 AA, zero critical axe issues **(M)**
- [ ] Lighthouse 100/100/100 on Home, Case, Watch and Proactive **(S)**
- [ ] A/B or sequential test of the new Home and Case surfaces **(M)**
- [ ] Roll out one surface at a time behind flags; keep old routes until stable **(M)**
- [ ] Design QA at 10 metres and 16:9/4:3 for the stage-linked screens **(S)**
- [ ] Post-launch review after two weeks; keep or revert per metric **(S)**
- [ ] Publish the design-system v1 and migration guide **(S)**

### 6.10 Stage refresh (optional, after the desk is stable)

- [ ] Keep the 90-second stage piece intact; do not force the daily shell onto it **(S)**
- [ ] Refresh typography and contrast for 10-metre legibility **(S)**
- [ ] Add a proactive second act with the same visual grammar as the desk **(M)**
- [ ] Record a fallback video of the refreshed stage **(S)**

---

## Acceptance gates

- [ ] A first-time engineer finds the top decision in **under 10 seconds**
- [ ] Time to first decision drops **≥ 30%** against the baseline
- [ ] **SUS ≥ 80** with five pilot users
- [ ] **WCAG 2.2 AA**; zero critical axe findings; keyboard-only core tasks
- [ ] **Lighthouse 100/100/100** on Home, Case, Watch and Proactive
- [ ] **LCP < 1.5 s, INP < 200 ms, CLS < 0.05** on the pilot laptop
- [ ] **No type below 11 px**; no 8 px labels anywhere
- [ ] **One primary accent**; colour only encodes meaning
- [ ] Command palette used by **≥ 70%** of engineers weekly
- [ ] Mobile triage succeeds **≥ 80%** one-handed
- [ ] The stage piece still runs in **90 seconds** and resets under five
- [ ] Defect-case task success does not regress

## Non-goals

- Neon cyberpunk, glassmorphism, 3D dashboards, animated backgrounds.
- A chatbot as the primary interface.
- Removing the stage piece’s theatrical language.
- Replacing every table with cards, or every card with a chart.
- Dark-only for daily use; the desk needs a light mode.
- Any AI action that changes the line, rejects a part or holds a batch automatically.
- Designing for the screenshot instead of the shift.

## Why this is worth doing

The product logic is already 2026: evidence-first, human-approved, proactive risk, cited AI, offline
on-site. The interface is the remaining gap. A design refresh does not add features; it makes the
existing decisions faster, calmer and more trustworthy — which is exactly what a quality manager
under pressure needs.

---
name: Requirement Radar
colors:
  surface: '#111317'
  surface-dim: '#111317'
  surface-bright: '#37393d'
  surface-container-lowest: '#0c0e11'
  surface-container-low: '#1a1c1f'
  surface-container: '#1e2023'
  surface-container-high: '#282a2d'
  surface-container-highest: '#333538'
  on-surface: '#e2e2e6'
  on-surface-variant: '#cbc3d7'
  inverse-surface: '#e2e2e6'
  inverse-on-surface: '#2f3034'
  outline: '#958ea0'
  outline-variant: '#494454'
  surface-tint: '#d0bcff'
  primary: '#d0bcff'
  on-primary: '#3c0091'
  primary-container: '#a078ff'
  on-primary-container: '#340080'
  inverse-primary: '#6d3bd7'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00a572'
  on-tertiary-container: '#00311f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#d0bcff'
  on-primary-fixed: '#23005c'
  on-primary-fixed-variant: '#5516be'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#111317'
  on-background: '#e2e2e6'
  surface-variant: '#333538'
typography:
  display:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Geist
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Geist
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: -0.01em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0em
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1.5rem
  gutter-desktop: 1.5rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
  space-2xl: 2rem
---

## Brand & Style

This design system establishes an exacting, analytical environment tailored for product managers, systems architects, and engineering leadership. The visual personality balances technical precision, uncompromising clarity, and quiet intelligence. It borrows cues from contemporary developer-first interfaces—understated structural architecture, surgical typography, and precise visual feedback that feels instantaneous and non-distracting.

The core visual methodology pairs high-density data clarity with atmospheric darkness. It avoids decorative ornamentation in favor of information salience: requirement ambiguity scores, structural gaps, and semantic validation checks surface through purposeful contrasts and sharp spatial boundaries rather than heavy skeuomorphism or loud gradients. The emotional tone conveys quiet authority, rigor, and proactive insight.

## Colors

The palette is engineered specifically for deep-focus analysis under dark-mode constraints, emphasizing structural layering over background luminance.

### Canvas & Surface Architecture
- **Base Background (`#080A0D`)**: The bedrock canvas for application roots and canvas borders.
- **Primary Surface (`#0F1217`)**: Base level for sidebars, workbench panels, and central content regions.
- **Secondary Surface (`#151922`)**: Nested groupings, tabular headers, grouped cards, and sidebar list containers.
- **Elevated Surface (`#1A1F29`)**: Contextual popovers, floating command bars, tooltips, and modal windows.
- **Subtle Surface / Hover (`#222834`)**: Subtle interactive state highlights on rows, tabs, and actionable badges.
- **Hairline Border (`#252B35`)**: The universal divider ensuring distinct plane separation without high-contrast visual noise.
- **Focus / Active Border (`#3B4454`)**: Active focus bounds, selected splitters, and hovered cards.

### Text & Contrast Hierarchy
- **Primary Text (`#F5F7FA`)**: Headings, requirement text strings, and active data points.
- **Secondary Text (`#9AA3B2`)**: Supporting attributes, labels, breadcrumbs, and interface controls.
- **Muted Text (`#697386`)**: Placeholder values, inactive states, keyboard shortcut keys, and timestamps.

### Intelligence & Diagnostic Semantics
- **AI & Smart Analysis (`#8B5CF6` / `#A78BFA`)**: Denotes syntactic parser recommendations, automated rewrite suggestions, and quality heuristics.
- **Critical / Ambiguity Violation (`#EF4444`)**: Unverifiable logic, contradictory clauses, missing test conditions.
- **Warning / Review Needed (`#F59E0B`)**: Weak modals (e.g., "should", "as appropriate"), passive voice, untracked dependencies.
- **Success / Passed (`#10B981`)**: Complete, testable, fully verified clauses.
- **Information / Telemetry (`#3B82F6`)**: Metadata references, cross-specification links, and pipeline sync points.

## Typography

The typographic hierarchy is built on Geist for structural UI, content evaluation, and natural language statements, while JetBrains Mono handles all programmatic references, semantic identifiers, keyboard accelerators, and system metrics.

- **Requirement Identifiers & Tokens**: Identifiers like `REQ-001`, `SRS-AUTH-04`, and validation hashes must be rendered in `code-md` or `code-sm` with tabular numerals enabled.
- **Density & Leading**: Requirement reading requires slightly more generous line-height than interface navigation to accommodate inline linting highlights, inline squiggly underlines, and badge chips without vertical collision.
- **Case Conventions**: `label-caps` is reserved exclusively for micro table headers, metric delta labels, and requirement state category flags.

## Layout & Spacing

The workspace uses a composite desktop architecture: a fixed navigation spine (56px collapsed / 240px expanded), an adjacent resizable entity/document tree pane (min 280px, max 420px), a flexible primary requirement canvas, and a contextual collapsible inspector drawer (360px default).

### Responsive Flow & Screen Densities
- **Desktop (1280px and above)**: Full triple-pane workspace. Content panes use a fluid layout separated by strict 1px boundary rules instead of gaps. Data tables and requirement feeds prioritize row density, with standard row heights resting at 36px (compact) and 48px (detailed).
- **Tablet / Laptop (1024px – 1279px)**: Inspector collapses into an overlay drawer. Document tree pane collapses into an icon shelf with flyout panels.
- **Mobile (< 1024px)**: Single-column linear layout. Sidebars switch to off-canvas sheets. Primary focus locks to isolated requirement inspection and alert triage.

### Spatial Rhythm
Internal component layouts honor an 8px base rhythm with 4px sub-intervals for high-density micro-alignment. Form inputs, table cells, and badges maintain horizontal padding independent of vertical margins to ensure precise label-to-border alignment.

## Elevation & Depth

Visual hierarchy does not use simulated drop shadows or skeuomorphic heights. Instead, depth is established strictly through tonal surface tiering, translucent glass overlays, and crisp hairline borders (`#252B35`).

### Layer Stack Architecture
1. **Canvas Level (0dp)**: Surface `#080A0D`. Serves as the canvas substrate and splitter gutter base.
2. **Structural Workspace (1dp)**: Surface `#0F1217` bounded by 1px solid `#252B35`. Contains requirement lists, tree viewers, and primary editors.
3. **Contained Groupings (2dp)**: Surface `#151922` bounded by 1px solid `#252B35`. Houses cards, metric summaries, and code diff callouts.
4. **Floating Overlays & Modals (3dp)**: Surface `#1A1F29` with a subtle alpha tint (`rgba(26, 31, 41, 0.94)`), a 12px backdrop blur, a 1px border of `#3B4454`, and an ambient diffused shadow: `0 16px 36px -8px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.04)`.
5. **Tooltips & Popovers (4dp)**: Surface `#1A1F29` with crisp single-pixel borders (`#3B4454`) and a focused ambient shadow: `0 4px 12px rgba(0, 0, 0, 0.5)`.

### Border Highlight System
Surfaces rely on subtle inset highlights rather than top lights. A 1px top border with `rgba(255, 255, 255, 0.05)` can be applied on primary elevated cards to define top-down lighting typical of refined desktop tools.

## Shapes

The design system adopts a soft, restrained corner radius (`0.25rem` / `4px` base) to project engineering rigor and compact efficiency.

- **Base Controls (Buttons, Inputs, Badges, Chips)**: `4px` border radius (`roundedness: 1`).
- **Cards, Panels, & Data Sections**: `6px` border radius (`rounded-lg`).
- **Dialog Windows, Floating Command Palettes, Flyouts**: `8px` border radius (`rounded-xl`).
- **Status Indicators & Micro Dots**: `9999px` (Full circle).

## Components

### Buttons
- **Primary Action (Solid AI / Main)**: Background `#8B5CF6`, text `#FFFFFF`, font `Geist` medium 13px, height 32px, px 12px, border radius 4px. Hover: `#7C3AED`. Active: `#6D28D9`.
- **Secondary / Default**: Background `#151922`, border 1px solid `#252B35`, text `#F5F7FA`. Hover: background `#1A1F29`, border `#3B4454`.
- **Ghost / Utility**: Background transparent, text `#9AA3B2`. Hover: background `#151922`, text `#F5F7FA`.
- **Destructive**: Background `rgba(239, 68, 68, 0.1)`, border 1px solid `rgba(239, 68, 68, 0.3)`, text `#EF4444`. Hover: background `rgba(239, 68, 68, 0.2)`.

### Chips & Semantic Status Badges
- **Requirement Token Badges**: Monospace `code-sm`, padding 2px 6px, border radius 4px.
  - *Critical Ambiguity*: Background `rgba(239, 68, 68, 0.1)`, text `#EF4444`, border `rgba(239, 68, 68, 0.25)`.
  - *Warning / Review*: Background `rgba(245, 158, 11, 0.1)`, text `#F59E0B`, border `rgba(245, 158, 11, 0.25)`.
  - *Passed / Valid*: Background `rgba(16, 185, 129, 0.1)`, text `#10B981`, border `rgba(16, 185, 129, 0.25)`.
  - *AI Recommendation*: Background `rgba(139, 92, 246, 0.12)`, text `#A78BFA`, border `rgba(139, 92, 246, 0.3)`.

### Requirement Cards & Row Items
- **List Rows**: Background transparent, bottom border 1px solid `#252B35`. Hover state changes background to `#151922`. Includes requirement ID in `code-md`, status badge, natural-language snippet, and inline score indicator.
- **Selected Row**: Background `#1A1F29`, left border accent 2px solid `#8B5CF6`.

### Inputs & Search Bars
- **Base Input**: Background `#0F1217`, border 1px solid `#252B35`, text `#F5F7FA`, placeholder `#697386`, height 32px, px 10px, radius 4px.
- **Focus State**: Border `#8B5CF6`, subtle box-shadow `0 0 0 1px #8B5CF6`, outline none.
- **Search Command Bar (Global / Linear-style)**: Height 40px, background `#151922`, border 1px solid `#3B4454`, prefix icon `#9AA3B2`, keyboard hint `JetBrains Mono` 11px wrapped in `#252B35` chip.

### Selection Controls (Checkboxes & Radios)
- **Checkboxes**: 14x14px box, border 1px solid `#3B4454`, radius 3px, background `#0F1217`. Checked: background `#8B5CF6`, border `#8B5CF6`, white micro checkmark.
- **Radio Buttons**: 14x14px circle, border 1px solid `#3B4454`, background `#0F1217`. Selected: border `#8B5CF6`, centered 6px dot `#8B5CF6`.

### Specialized Domain Components
- **Ambiguity Heatmap Bar**: A segmented 4px high multi-state progress line embedded directly into requirement headers (Green = Crisp, Amber = Questionable, Red = Unclear).
- **Inline Recommendation Callout**: Embedded directly beneath a flagged sentence in the SRS editor. Background `#151922`, left accent border 2px solid `#8B5CF6`, radius 0 4px 4px 0, padding 8px 12px. Displays flagged term, suggested replacement, and quick-action "Apply Fix" (`Tab`) button.
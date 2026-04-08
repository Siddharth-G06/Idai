# Design System Strategy: The Sovereign Lens

## 1. Overview & Creative North Star
**Creative North Star: The Sovereign Lens**
The Sovereign Lens is a design philosophy that moves away from the "cluttered utility" of traditional fintech and toward "curated intelligence." In this design system, we treat data as a luxury asset. We reject the rigid, boxy constraints of standard dashboards in favor of an editorial layout characterized by intentional asymmetry, significant breathing room, and atmospheric depth.

To break the "template" look, designers should utilize **Overlapping Composition**. Metrics should not just sit in grids; they should layer over subtle glass textures, with display typography that commands attention through scale rather than weight. The goal is a UI that feels "whispered" rather than shouted—where premium quality is found in the precision of the spacing and the depth of the shadows.

---

## 2. Colors & Surface Philosophy
The palette is rooted in a deep, nocturnal navy, providing a high-contrast stage for our precision accents: Emerald (Growth/Stability) and Deep Red (Urgency/Action).

### The "No-Line" Rule
Standard UI relies on 1px solid borders to define sections. **In this system, 1px solid borders are strictly prohibited for sectioning.** Boundaries must be defined through:
*   **Background Shifts:** Using `surface-container-low` against `surface` to imply a new zone.
*   **Tonal Transitions:** Defining edges through subtle variations in darkness.

### Surface Hierarchy & Nesting
Think of the UI as a physical stack of semi-transparent materials.
*   **Base:** `surface` (#061423) is the floor.
*   **Sub-sections:** Use `surface-container-low` for large content areas.
*   **Actionable Cards:** Use `surface-container-high` or `surface-container-highest` to "lift" the content toward the user.
*   **Nesting:** An inner module (like a data table) inside a card should use a *lower* tier (e.g., `surface-container-lowest`) to create a "recessed" look, adding architectural complexity.

### The "Glass & Gradient" Rule
To achieve the Fintech Luxury aesthetic, floating elements (modals, popovers, navigation) must use **Glassmorphism**:
*   **Fill:** `surface_variant` at 40-60% opacity.
*   **Effect:** `backdrop-blur` (20px - 40px).
*   **Signature Texture:** Main CTAs should never be flat. Apply a subtle linear gradient from `primary` to `primary_container` at a 135-degree angle to provide a metallic, high-end sheen.

---

## 3. Typography
We use a dual-typeface system to balance authority with technical precision.

*   **Display & Headlines (Manrope):** This is our "Editorial" voice. Manrope’s geometric builds feel modern and expensive. Use `display-lg` for hero metrics and `headline-md` for section titles. Do not be afraid of massive scale—large, thin headers create a premium feel.
*   **Body & Labels (Inter):** Inter is our "Functional" voice. It provides the Swiss-style readability required for complex data.
*   **Hierarchy Tip:** Pair a `display-sm` metric with a `label-sm` (all caps, tracked out 10%) description to create a sophisticated, data-driven contrast.

---

## 4. Elevation & Depth
In this system, elevation is conveyed through **Tonal Layering** and light simulation, not structural lines.

*   **The Layering Principle:** Avoid shadows on static cards. Achieve depth by stacking surface tokens. A `surface-container-highest` card on a `surface` background provides enough contrast to be felt without being seen.
*   **Ambient Shadows:** For floating elements (menus, tooltips), use a shadow color tinted with navy (`#020F1E`) rather than black.
    *   *Blur:* 40px - 80px.
    *   *Opacity:* 6% - 10%.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility, use a **Ghost Border**: `outline_variant` at 15% opacity. This creates a "glint" on the edge of the glass rather than a hard container line.

---

## 5. Components

### Buttons
*   **Primary:** Pill-shaped (`rounded-full`), using the signature Red gradient. Text should be `on-primary`, bold, and centered.
*   **Secondary:** Glass-pill. Semi-transparent `surface-variant` with a `Ghost Border`.
*   **Tertiary:** No background. `label-md` styling with a subtle hover state using `on-surface-variant`.

### Glass Cards
*   **Structure:** No dividers. Use `padding-xl` (2rem) to let content breathe.
*   **Header:** Use `title-lg` for card titles, left-aligned to create an asymmetrical "editorial" start point.

### Data Inputs
*   **Field:** `surface-container-highest` with a 15% `outline-variant` border.
*   **Focus State:** Transition the border to `secondary` (Emerald) and add a subtle inner glow.
*   **Shape:** `rounded-md` (1.5rem) to maintain a soft, premium feel.

### Selection & Chips
*   **Filter Chips:** Pill-shaped. Unselected states should be nearly invisible (`surface-container-low`). Selected states use `secondary_container` with `on-secondary-container` text.

### The "Invisible" List
*   **Rule:** Forbid the use of horizontal divider lines. 
*   **Alternative:** Separate list items with `0.75rem` of vertical white space. Use a `surface-container-low` hover state with `rounded-sm` (0.5rem) corners to highlight the active row.

---

## 6. Do’s and Don’ts

### Do:
*   **DO** use whitespace as a luxury. If a dashboard feels "full," increase the padding.
*   **DO** use the `secondary` (Emerald) for all positive data trends to reinforce the "Trustworthy" pillar.
*   **DO** lean into asymmetry. A large metric on the left balanced by a small chart on the right feels more bespoke than two equal columns.

### Don't:
*   **DON'T** use 100% white for body text. Use `on-surface-variant` to keep the UI "moody" and easy on the eyes.
*   **DON'T** use standard drop shadows. If it looks like a "box shadow," it's too heavy.
*   **DON'T** use sharp corners. Every element should feel smoothed and "polished," adhering to the `roundedness` scale provided.
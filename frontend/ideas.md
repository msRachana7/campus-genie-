# Campus Genie design direction

## Approach 1
**Theme Name:** Chalkboard Orbit

**Very Brief Intro:** A warm, editorial campus dashboard that mixes paper textures, blackboard notes, and energetic chart marks. It feels like a clever student planner that grew into a living campus map.

**Probability:** 0.07

## Approach 2
**Theme Name:** Neon Noticeboard

**Very Brief Intro:** A dark, kinetic campus signal room with electric accents, live activity pulses, and playful data widgets. It feels contemporary and high-energy, but intentionally stays focused on student utility rather than gaming.

**Probability:** 0.03

## Approach 3
**Theme Name:** Orchard Commons

**Very Brief Intro:** A bright, tactile digital commons inspired by campus trees, printed club posters, and colored index cards. It makes discovery feel social, optimistic, and a little serendipitous without becoming childish.

**Probability:** 0.08

# Chosen approach: Orchard Commons

## Design Movement
Contemporary editorial brutalism softened by community bulletin-board warmth: assertive typography, offset cards, print-like labels, and generous breathing room, balanced with friendly rounded illustrations and calm data surfaces.

## Core Principles
1. **Discovery over density:** every screen should reveal a next step, not present a wall of data.
2. **Tactile campus artifacts:** cards, chips, tabs, pins, and index-like labels should feel collected from real student life.
3. **Asymmetric energy:** use a strong left rail, offset hero composition, and varied card proportions instead of a generic centered dashboard.
4. **Warm intelligence:** analytics and chat should feel human, optimistic, and legible rather than clinical.

## Color Philosophy
The palette uses a deep ink green as the grounding campus color, warm oat as the paper field, and a signature mango-coral as the social spark. Leaf green and sky blue indicate momentum and trust; dusty lilac is reserved for reflective history moments. The colors should feel like sunlight on noticeboards and highlighter marks in a well-used notebook, not like a generic SaaS gradient.

## Layout Paradigm
A desktop-first asymmetric shell: a narrow fixed left rail for identity and navigation, a wide scrollable content canvas, and a right-side insight stack that behaves like a live campus bulletin. The home view opens with a side-positioned avatar and a skewed welcome card, then branches into discovery cards and live signals. Mobile collapses to a top bar plus horizontally scrolling navigation.

## Signature Elements
- A tiny **spark pin** motif used for live, social, and archival states.
- Offset paper cards with one clipped corner or underlined marker accent.
- A friendly **Genie orb/avatar** rendered as a soft illustrated character with a mango halo, never centered as the only focal point.

## Interaction Philosophy
Interactions should reward curiosity. Tabs slide with a small marker trail, cards lift slightly on hover, and “Ask Genie” actions carry forward the context of the selected resource or post. Empty states should suggest a question or a route, never merely report that nothing exists.

## Animation
Use 160–260ms transitions with a custom ease-out. On first load, content enters in staggered groups from 0.98 scale and 12px vertical offset. Live pulse dots breathe subtly; chart bars rise only on initial mount; chat replies appear with a compact paper-slip reveal. Respect reduced motion and keep high-frequency hover interactions quiet.

## Typography System
Use **Space Grotesk** for display headings and navigation labels, with **DM Sans** for readable body text and data labels. Headings should use tight tracking and occasional italic emphasis; body copy should stay 14–16px with relaxed line height. Numeric insights use Space Grotesk medium with tabular-looking spacing.

## Brand Essence
**Campus Genie is the warm intelligence layer for BMSCE students who want to find their people, resources, and place on campus without searching five different channels.** Personality: curious, generous, quietly clever.

## Brand Voice
Headlines should be direct, lightly playful, and specific. CTAs should sound like invitations into a useful next move, never generic conversion copy. Microcopy should make the system feel observant but respectful.

Example lines: “Your campus has a lot going on. Let’s make it findable.” and “Ask about the fest, the syllabus, or the friend you haven’t met yet.”

## Wordmark & Logo
A compact hand-drawn-looking **CG spark-pin**: a four-point mango star nested into a dark green location pin, with a small cutout dot suggesting a chat bubble. The wordmark uses Space Grotesk semibold with a custom offset “G” underline; it should not be typeset as a default logo treatment.

## Signature Brand Color
**Mango Signal — #F4A261**, a warm orange that marks moments of discovery, social energy, and “Genie has a lead for you.”

## Style Decisions
- Use a warm oat canvas instead of white.
- Keep the left rail dark ink green and the content cards tactile but restrained.
- Use generated custom imagery only for the avatar/brand mark and the archival hero; use CSS/iconography for the rest so the interface stays crisp and product-like.
- No fake testimonials, ratings, or reviews.

- Entry screens should balance the auth form with an asymmetric campus artifact or insight note, rather than presenting a lone centered SaaS card.
- The Campus Genie wordmark should foreground the CG spark-pin and include a handmade cue such as an offset underline.
- Primary surfaces should carry at least one restrained tactile gesture: clipped corner, pinned label, marker underline, or index-card treatment.

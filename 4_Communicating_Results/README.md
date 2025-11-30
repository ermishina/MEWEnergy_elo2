# M4. Communicating Results — Solar PV + Battery Decision Support

This milestone translates our analysis into audience-fit messaging and artifacts that help U.S. homeowners decide whether rooftop solar plus a battery is worth it for them.

## Target audience
- **Who:** Homeowners ages 30–65 in high-tariff or outage-prone states (CA, TX, FL), monthly bill \$120–\$300, mobile-first, active in HOA/neighborhood chats, moderate digital literacy, limited time.
- **Motivations:** Lower bills and keep critical loads on during outages; open to data-backed guidance but skeptical of sales pitches.
- **Constraints:** Avoids jargon; wants a quick “Is this worth it?” read before deeper detail; may not know their exact tariff or load shape.

## Learning goals and desired actions
- See ZIP-specific **savings and payback ranges** that include the 25D tax credit and realistic system costs.
- Understand **resilience value** (hours of backup by battery size) alongside bill impacts.
- Recognize **uncertainty drivers**: tariff assumptions, weather variance, load profile guesses; know which inputs they can verify.
- **Actions to prompt:** run the address-based check, choose an “outage-ready” preset, schedule a follow-up call, and share the summary with neighbors/HOA.

## Communication artifact
- **Medium:** Mobile-first landing page with an embedded scenario snapshot (from the `scripts/` prototype) plus a printable 2-page brief for HOA/email/WhatsApp distribution.
- **Rationale:** Fits mobile habits, quick to skim, localized by ZIP to build trust, easy to forward in group chats.
- **Planned contents:** hero grounded in local data, 3-card savings/payback bands (best/base/conservative), outage resilience explainer, CTA buttons (“Check my address”, “Book a call”), and a caveats/assumptions sidebar.
- **Location:** `3_reports/m4_communication/artifacts/` (PDF/layout assets and any exported visuals).

## Handling uncertainty
- Present **ranges instead of point estimates** for production, savings, and payback; note what drives the spread.
- Flag where we **assumed tariffs or load shapes**; ask users to confirm their rate plan before acting.
- Use plain caveat language: “If you use more power at night, savings may be closer to the low end.”
- Include a short **“What we don’t know yet”** section to keep expectations realistic.

## Distribution and measurement
- **Channels:** HOA email chains, neighborhood Facebook/Nextdoor posts, WhatsApp groups; optional follow-up calls or webinars for deeper questions.
- **Timing:** Ahead of peak summer/winter usage and known outage seasons in target regions.
- **Metrics:** address checks started/completed, CTA clicks to book a call, brief downloads/opens, time on page, and feedback on clarity/trust.

## Dependencies and data inputs
- PVWatts (v8) production ranges, URDB/NREL tariff data, and system cost/load assumptions from prior analysis.
- Visuals generated via the Flask prototype in `scripts/` (requires `NREL_API_KEY` in `.env`; see `scripts/README.md`).

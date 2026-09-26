-- The Lens — shared database standard ("the spine"). DRAFT v0, 2026-09-26.
--
-- This is the fixed shape every Lens lab uses. It is DOMAIN-NEUTRAL by design:
-- no subject-specific columns, no proprietary vocabulary. A lab maps its domain
-- INTO these neutral slots (via injected config), rather than changing the shape.
--
-- Modeled (nearly-decomposable architecture) on the PROVES reference spine
-- (staging_extractions -> validation_decisions -> core_entities + lineage +
-- agent oversight), generalized. Names here are neutral placeholders; refine with
-- the operator before first use.
--
-- The three-step spine: candidates -> decisions -> verified.
-- Plus: sources (lineage) and an oversight set (for agent-assisted labs).

-- ---------------------------------------------------------------------------
-- Lineage: where a candidate came from (kept separate from the claim itself).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    id            uuid PRIMARY KEY,
    uri           text,                 -- where the material was read from
    snapshot      jsonb,                -- raw captured payload (for audit)
    fetched_at    timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Candidates (the inbox): raw findings, captured but NOT yet true.
-- Written by intake; read by review. Classification is set at capture time.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidates (
    id            uuid PRIMARY KEY,
    source_id     uuid REFERENCES sources(id),
    kind          text NOT NULL,        -- neutral type set, defined per lab (injected)
    payload       jsonb NOT NULL,       -- the finding
    evidence      jsonb,                -- quote/reference supporting it
    confidence    real,
    status        text NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','accepted','rejected','needs_context','merged')),
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Decisions (append-only review log): every accept/reject/edit/merge/flag.
-- Written by review (human or agent); the audit trail.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decisions (
    id            uuid PRIMARY KEY,
    candidate_id  uuid NOT NULL REFERENCES candidates(id),
    action        text NOT NULL
                    CHECK (action IN ('accept','reject','edit','merge','flag')),
    actor         text NOT NULL,        -- who decided
    actor_kind    text NOT NULL DEFAULT 'human'
                    CHECK (actor_kind IN ('human','agent')),
    reason        text,
    before        jsonb,
    after         jsonb,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Verified (the library): human-established truth, versioned.
-- Written by promotion (from an accepted candidate); read by serve.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS verified (
    id             uuid PRIMARY KEY,
    canonical_key  text NOT NULL,
    kind           text NOT NULL,
    payload        jsonb NOT NULL,
    provenance     jsonb,               -- source_id + decision trail
    is_current     boolean NOT NULL DEFAULT true,
    superseded_by  uuid REFERENCES verified(id),
    verified_by    text,
    verified_at    timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Oversight (optional, for agent-assisted labs): capabilities, proposals, trust.
-- A self-contained set; mediated by the review/promotion path.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS oversight_capabilities (
    id                    uuid PRIMARY KEY,
    agent_name            text NOT NULL,
    capability_type       text NOT NULL,
    trust_score           real NOT NULL DEFAULT 0,
    auto_approve_threshold real,
    requires_review       boolean NOT NULL DEFAULT true,
    UNIQUE (agent_name, capability_type)
);

CREATE TABLE IF NOT EXISTS oversight_proposals (
    id             uuid PRIMARY KEY,
    capability_id  uuid REFERENCES oversight_capabilities(id),
    proposed       jsonb NOT NULL,
    rationale      text,
    status         text NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','approved','rejected','auto_approved','implemented','reverted')),
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS oversight_trust_history (
    id             uuid PRIMARY KEY,
    capability_id  uuid REFERENCES oversight_capabilities(id),
    delta          real NOT NULL,
    reason         text,
    created_at     timestamptz NOT NULL DEFAULT now()
);

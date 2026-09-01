-- Run once in Supabase SQL Editor (Project > SQL Editor > New query).
-- Replaces the local story_queue/ folder + story_state.json with cloud tables
-- so GitHub Actions (ephemeral runners) can share state across scheduled runs.

create table if not exists story_queue (
    id bigint generated always as identity primary key,
    variant text not null default 'short',   -- 'short' = 9:16 Shorts/Reels, 'long' = 16:9 YouTube
    theme text not null,
    title text not null,
    payload jsonb not null,       -- full story dict (story, keywords, dna, publishing_kit, ...)
    created_at timestamptz not null default now(),
    claimed_at timestamptz,
    rendered boolean not null default false,
    youtube_id text,
    instagram_id text,
    error text
);

create table if not exists story_state (
    id bigint generated always as identity primary key,
    variant text not null default 'short',
    theme text not null,
    title text not null,
    hook text,
    relationship text,
    conflict text,
    emotion text,
    payoff text,
    fingerprint text,
    curve text,
    score int,
    tracking_tag text,
    youtube_id text,
    instagram_id text,
    created_at timestamptz not null default now()
);

-- Composite so each variant's renderer scans only its own unclaimed rows.
create index if not exists story_queue_unclaimed_idx
    on story_queue (variant, id) where claimed_at is null;

-- ---------------------------------------------------------------------------
-- Migrations for an existing project. Safe to re-run.
-- ---------------------------------------------------------------------------

-- (a) Instagram support:
-- alter table story_queue add column if not exists instagram_id text;
-- alter table story_state add column if not exists instagram_id text;

-- (b) Long-form variant. RUN THIS BEFORE DEPLOYING THE LONG-FORM CODE — the
--     renderer filters on `variant`, so the column must exist first or the
--     short pipeline stops matching rows and stops posting.
--     `default 'short'` backfills every existing row correctly.
--
-- alter table story_queue add column if not exists variant text not null default 'short';
-- alter table story_state add column if not exists variant text not null default 'short';
--
-- alter table story_queue drop constraint if exists story_queue_variant_chk;
-- alter table story_queue add constraint story_queue_variant_chk
--     check (variant in ('short','long'));
--
-- drop index if exists story_queue_unclaimed_idx;
-- create index if not exists story_queue_unclaimed_idx
--     on story_queue (variant, id) where claimed_at is null;

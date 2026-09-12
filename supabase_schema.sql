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

-- ---------------------------------------------------------------------------
-- story_metrics: performance snapshots, one row per video per collection day.
--
-- story_state records what we published; this records how it did. The two join
-- on youtube_id, which is what makes the STORY_ENGINE_BIBLE batch analysis a
-- query rather than an afternoon in YouTube Studio -- every DNA dimension the
-- bible wants to sort by (hook class, ending type, theme) is already a column
-- on story_state.
--
-- Snapshots rather than a single mutable row: a Short's view count keeps moving
-- for weeks, so "views on day 3" and "views on day 30" are different questions
-- and both are worth answering. Re-running collection on the same day updates
-- that day's row instead of adding a duplicate.
-- ---------------------------------------------------------------------------
create table if not exists story_metrics (
  id bigserial primary key,
  youtube_id text not null,
  collected_on date not null default current_date,
  -- Data API (public counters)
  views bigint,
  likes bigint,
  comments bigint,
  -- Analytics API (owner-only; null until the yt-analytics.readonly scope is
  -- granted, so the table is useful before the token is re-consented)
  estimated_minutes_watched numeric,
  average_view_duration_seconds numeric,
  average_view_percentage numeric,
  collected_at timestamptz not null default now(),
  unique (youtube_id, collected_on)
);

create index if not exists story_metrics_youtube_idx on story_metrics (youtube_id);

-- ---------------------------------------------------------------------------
-- ig_token: the live Instagram access token, kept rolling by refresh_ig_token.py.
--
-- Instagram long-lived tokens last 60 days and CANNOT be refreshed once expired
-- -- recovery means minting a new one by hand in the Meta dashboard, which is
-- what 2026-09-11 cost. A weekly job refreshes this well ahead of the deadline.
--
-- It lives here rather than in the IG_ACCESS_TOKEN GitHub secret because a
-- workflow cannot rewrite a repo secret without a PAT carrying repo-wide
-- "Secrets: read and write" -- a much heavier credential than this job needs.
-- The env var remains the seed for the first refresh and the fallback if the
-- stored token ever lapses.
--
-- Single row by construction; RLS is on, so only the service key reaches it.
-- ---------------------------------------------------------------------------
create table if not exists ig_token (
  id int primary key default 1,
  access_token text not null,
  expires_at timestamptz not null,
  refreshed_at timestamptz not null default now(),
  constraint ig_token_singleton check (id = 1)
);
alter table ig_token enable row level security;

-- Run once in Supabase SQL Editor (Project > SQL Editor > New query).
-- Replaces the local story_queue/ folder + story_state.json with cloud tables
-- so GitHub Actions (ephemeral runners) can share state across scheduled runs.

create table if not exists story_queue (
    id bigint generated always as identity primary key,
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

create index if not exists story_queue_unclaimed_idx on story_queue (id) where claimed_at is null;

-- Migration: if you already ran this file once (before Instagram support was
-- added), just run these two lines instead of the whole file:
-- alter table story_queue add column if not exists instagram_id text;
-- alter table story_state add column if not exists instagram_id text;

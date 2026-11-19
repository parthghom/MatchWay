-- Run this once in the Supabase SQL editor (Project -> SQL editor -> New query -> Run).
-- It makes sure the "reviews" table can hold everything the EMA rating system needs.
-- The server rebuilds every rider's and driver's rating from this table when it starts,
-- so a restart (for example on Render) never loses a rating.

create table if not exists public.reviews (
  id          bigint generated always as identity primary key,
  ride_id     text        not null,
  reviewer_id text        not null,   -- user id of the person who rated
  target_id   text        not null,   -- user id of the person who was rated (rider or driver)
  stars       integer     not null check (stars between 1 and 5),
  target_role text,                   -- 'driver' or 'rider'
  created_at  timestamptz not null default now()
);

-- if the table already existed from before, add what it may be missing
alter table public.reviews add column if not exists target_role text;
alter table public.reviews add column if not exists created_at timestamptz not null default now();
alter table public.reviews add column if not exists id bigint generated always as identity;

create index if not exists reviews_target_idx on public.reviews (target_id);
create index if not exists reviews_created_idx on public.reviews (created_at);

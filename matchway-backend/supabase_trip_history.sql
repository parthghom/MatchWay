-- Run this once in the Supabase SQL editor (Project -> SQL editor -> New query -> Run).
-- It makes the table that keeps every finished trip, so ride history survives a server restart.
-- The server reads it when it starts and puts each person's trips back onto their Stack.

create table if not exists public.trip_history (
  id         bigint generated always as identity primary key,
  role       text        not null check (role in ('rider', 'driver')),
  user_id    text        not null,
  trip_id    text        not null,
  trip       jsonb       not null,
  created_at timestamptz not null default now(),
  unique (role, user_id, trip_id)
);

create index if not exists trip_history_person_idx on public.trip_history (role, user_id, created_at);

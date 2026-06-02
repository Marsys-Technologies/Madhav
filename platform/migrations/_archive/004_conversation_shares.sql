-- ─── Conversation shares (public read-only links) ────────────────────────────

create table public.conversation_shares (
  id              uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  slug            text not null unique,
  created_by      uuid not null references public.profiles(id) on delete cascade,
  created_at      timestamptz default now(),
  expires_at      timestamptz,
  revoked_at      timestamptz
);

create index on public.conversation_shares(conversation_id);

alter table public.conversation_shares enable row level security;

-- All access via service role API routes.
create policy "conversation_shares: astrologer all" on public.conversation_shares
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );
create policy "conversation_shares: creator select" on public.conversation_shares
  for select using (created_by = auth.uid());

-- ─── Message feedback (thumbs up / down) ─────────────────────────────────────

create table public.message_feedback (
  id              uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  message_id      text not null,
  user_id         uuid not null references public.profiles(id) on delete cascade,
  rating          smallint not null check (rating in (-1, 1)),
  comment         text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  unique(message_id, user_id)
);

create index on public.message_feedback(conversation_id);

create trigger trg_message_feedback_updated_at
  before update on public.message_feedback
  for each row execute procedure public.set_updated_at();

alter table public.message_feedback enable row level security;

-- All access via service role API routes (same pattern as messages).
create policy "message_feedback: astrologer all" on public.message_feedback
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );

-- ─── Chat attachments ─────────────────────────────────────────────────────────

create table public.chat_attachments (
  id              uuid primary key default gen_random_uuid(),
  conversation_id uuid references public.conversations(id) on delete cascade,
  message_id      text,
  user_id         uuid not null references public.profiles(id) on delete cascade,
  storage_path    text not null,
  mime            text not null,
  size_bytes      bigint not null,
  created_at      timestamptz default now()
);

create index on public.chat_attachments(conversation_id);
create index on public.chat_attachments(user_id);

alter table public.chat_attachments enable row level security;

create policy "chat_attachments: astrologer all" on public.chat_attachments
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );
create policy "chat_attachments: client own" on public.chat_attachments
  for select using (user_id = auth.uid());

-- Storage bucket for chat attachments (private; 30 MB; images + PDF).
-- `on conflict` keeps the migration idempotent for rerun / CI environments.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'chat-attachments',
  'chat-attachments',
  false,
  31457280,
  array['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'application/pdf']
)
on conflict (id) do nothing;

-- Storage RLS — owner-scoped. The first path segment is the user id (see upload route).
create policy "chat-attachments: owner read"
  on storage.objects for select
  using (
    bucket_id = 'chat-attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "chat-attachments: owner insert"
  on storage.objects for insert
  with check (
    bucket_id = 'chat-attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "chat-attachments: owner delete"
  on storage.objects for delete
  using (
    bucket_id = 'chat-attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

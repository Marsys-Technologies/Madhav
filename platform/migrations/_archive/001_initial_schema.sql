-- profiles: extends auth.users
create table public.profiles (
  id          uuid primary key references auth.users on delete cascade,
  role        text not null check (role in ('astrologer', 'client')) default 'client',
  name        text,
  created_at  timestamptz default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into public.profiles (id, role, name)
  values (
    new.id,
    case when new.email = current_setting('app.astrologer_email', true) then 'astrologer' else 'client' end,
    coalesce(new.raw_user_meta_data->>'full_name', new.email)
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- charts
create table public.charts (
  id           uuid primary key default gen_random_uuid(),
  client_id    uuid not null references public.profiles(id) on delete cascade,
  name         text not null,
  birth_date   date not null,
  birth_time   time not null,
  birth_place  text not null,
  birth_lat    numeric,
  birth_lng    numeric,
  ayanamsa     text default 'lahiri',
  house_system text default 'sripathi',
  created_at   timestamptz default now()
);

-- pyramid_layers
create table public.pyramid_layers (
  id         uuid primary key default gen_random_uuid(),
  chart_id   uuid not null references public.charts(id) on delete cascade,
  layer      text not null,
  sublayer   text not null,
  status     text not null default 'not_started'
             check (status in ('not_started', 'in_progress', 'complete')),
  version    text,
  updated_at timestamptz default now(),
  unique(chart_id, layer, sublayer)
);

-- documents
create table public.documents (
  id           uuid primary key default gen_random_uuid(),
  chart_id     uuid not null references public.charts(id) on delete cascade,
  layer        text not null,
  name         text not null,
  storage_path text not null,
  version      text not null default '1.0',
  created_at   timestamptz default now(),
  updated_at   timestamptz default now(),
  unique(chart_id, name)
);

-- conversations
create table public.conversations (
  id         uuid primary key default gen_random_uuid(),
  chart_id   uuid not null references public.charts(id) on delete cascade,
  user_id    uuid not null references public.profiles(id) on delete cascade,
  module     text not null check (module in ('build', 'consume')),
  title      text,
  created_at timestamptz default now()
);

-- messages
create table public.messages (
  id              uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  role            text not null check (role in ('user', 'assistant', 'tool')),
  content         text,
  tool_calls      jsonb,
  created_at      timestamptz default now()
);

-- reports
create table public.reports (
  id           uuid primary key default gen_random_uuid(),
  chart_id     uuid not null references public.charts(id) on delete cascade,
  domain       text not null,
  title        text not null,
  storage_path text not null,
  version      text not null default '1.0',
  created_at   timestamptz default now(),
  updated_at   timestamptz default now(),
  unique(chart_id, domain)
);

-- ─── Indexes ──────────────────────────────────────────────────────────────────

create index on public.charts(client_id);
create index on public.conversations(chart_id);
create index on public.conversations(user_id);
create index on public.messages(conversation_id);
create index on public.messages(conversation_id, created_at);

-- ─── updated_at trigger ───────────────────────────────────────────────────────

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_pyramid_layers_updated_at
  before update on public.pyramid_layers
  for each row execute procedure public.set_updated_at();

create trigger trg_documents_updated_at
  before update on public.documents
  for each row execute procedure public.set_updated_at();

create trigger trg_reports_updated_at
  before update on public.reports
  for each row execute procedure public.set_updated_at();

-- ─── RLS ──────────────────────────────────────────────────────────────────────

alter table public.profiles enable row level security;
alter table public.charts enable row level security;
alter table public.pyramid_layers enable row level security;
alter table public.documents enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.reports enable row level security;

-- profiles: own row only
create policy "profiles: read own" on public.profiles
  for select using (auth.uid() = id);
create policy "profiles: update own" on public.profiles
  for update using (auth.uid() = id);

-- charts: astrologer sees all; clients see only their own
create policy "charts: astrologer all" on public.charts
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );
create policy "charts: client own" on public.charts
  for select using (client_id = auth.uid());

-- pyramid_layers, documents, reports: same pattern
create policy "pyramid_layers: astrologer all" on public.pyramid_layers
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );
create policy "pyramid_layers: client read own" on public.pyramid_layers
  for select using (
    exists (select 1 from public.charts where id = chart_id and client_id = auth.uid())
  );

create policy "documents: astrologer all" on public.documents
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );
create policy "documents: client read own" on public.documents
  for select using (
    exists (select 1 from public.charts where id = chart_id and client_id = auth.uid())
  );

create policy "reports: astrologer all" on public.reports
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );
create policy "reports: client read own" on public.reports
  for select using (
    exists (select 1 from public.charts where id = chart_id and client_id = auth.uid())
  );

-- conversations, messages: no client-side access (all via service role API routes)
create policy "conversations: astrologer all" on public.conversations
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );
create policy "messages: astrologer all" on public.messages
  for all using (
    exists (select 1 from public.profiles where id = auth.uid() and role = 'astrologer')
  );

-- Storage bucket (run in Supabase dashboard Storage tab)
-- Bucket name: chart-documents, private

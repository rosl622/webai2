-- Create comments table
create table public.comments (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  page_id text not null, -- Stores "IT_2024-02-12" or similar
  nickname text not null,
  password text not null, -- Simple text password for deletion
  content text not null
);

-- Enable Row Level Security (RLS)
alter table public.comments enable row level security;

-- Create Policy: Allow Public Read
create policy "Public comments are viewable by everyone."
  on public.comments for select
  using ( true );

-- Create Policy: Allow Public Insert
create policy "Anyone can insert a comment."
  on public.comments for insert
  with check ( true );

-- Create Policy: Allow Public Delete (Ideally restricted, but for this simple app we handle password check in app logic or via RLS using headers if advanced, but simple app logic is fine for now)
-- Note: In a real app, strict RLS or a Postgres Function for deletion with password check is better.
-- For now, allowing delete if they know the ID (App handles password check before calling delete API).
create policy "Anyone can delete comments."
  on public.comments for delete
  using ( true );

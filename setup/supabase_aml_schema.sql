create table public.aml_transactions (
  id bigserial not null,
  transaction_id text not null,
  account_id text null,
  amount numeric(15, 2) null,
  currency text null default 'USD'::text,
  transaction_type text null,
  transaction_date date null,
  beneficiary_account text null,
  beneficiary_name text null,
  beneficiary_bank text null,
  beneficiary_country text null,
  origin_country text null,
  purpose text null,
  status text null default 'PENDING'::text,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint aml_transactions_pkey primary key (id),
  constraint aml_transactions_transaction_id_key unique (transaction_id)
) TABLESPACE pg_default;

create index IF not exists idx_aml_transactions_date on public.aml_transactions using btree (transaction_date) TABLESPACE pg_default;

create index IF not exists idx_aml_transactions_status on public.aml_transactions using btree (status) TABLESPACE pg_default;

create index IF not exists idx_aml_transactions_beneficiary on public.aml_transactions using btree (beneficiary_name) TABLESPACE pg_default;

create index IF not exists idx_aml_transactions_country on public.aml_transactions using btree (beneficiary_country) TABLESPACE pg_default;

create trigger update_aml_transactions_updated_at BEFORE
update on aml_transactions for EACH row
execute FUNCTION update_updated_at_column ();

create table public.aml_alerts (
  id bigserial not null,
  alert_id text not null,
  subject_id text null,
  subject_type text null default 'TRANSACTION'::text,
  typology text null,
  risk_score numeric(3, 2) null,
  evidence jsonb null,
  status text null default 'ACTIVE'::text,
  assigned_to text null,
  resolution text null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint aml_alerts_pkey primary key (id),
  constraint aml_alerts_alert_id_key unique (alert_id)
) TABLESPACE pg_default;

create index IF not exists idx_aml_alerts_status on public.aml_alerts using btree (status) TABLESPACE pg_default;

create index IF not exists idx_aml_alerts_typology on public.aml_alerts using btree (typology) TABLESPACE pg_default;

create index IF not exists idx_aml_alerts_subject on public.aml_alerts using btree (subject_id) TABLESPACE pg_default;

create index IF not exists idx_aml_alerts_risk_score on public.aml_alerts using btree (risk_score) TABLESPACE pg_default;

create trigger update_aml_alerts_updated_at BEFORE
update on aml_alerts for EACH row
execute FUNCTION update_updated_at_column ();


create table public.sanctions (
  id bigserial not null,
  entity_id text not null,
  name text not null,
  name_normalized text not null,
  schema_type text null default 'Person'::text,
  countries jsonb null default '[]'::jsonb,
  topics jsonb null default '[]'::jsonb,
  datasets jsonb null default '[]'::jsonb,
  first_seen date null,
  last_seen date null,
  properties jsonb null default '{}'::jsonb,
  data_source text null default 'OpenSanctions'::text,
  list_name text null default 'unknown'::text,
  program text null default 'unknown'::text,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint sanctions_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_sanctions_name on public.sanctions using btree (name) TABLESPACE pg_default;

create index IF not exists idx_sanctions_name_normalized on public.sanctions using btree (name_normalized) TABLESPACE pg_default;

create index IF not exists idx_sanctions_entity_id on public.sanctions using btree (entity_id) TABLESPACE pg_default;

create index IF not exists idx_sanctions_list_name on public.sanctions using btree (list_name) TABLESPACE pg_default;

create index IF not exists idx_sanctions_data_source on public.sanctions using btree (data_source) TABLESPACE pg_default;

create index IF not exists idx_sanctions_name_search on public.sanctions using gin (to_tsvector('english'::regconfig, name)) TABLESPACE pg_default;

create trigger update_sanctions_updated_at BEFORE
update on sanctions for EACH row
execute FUNCTION update_updated_at_column ();
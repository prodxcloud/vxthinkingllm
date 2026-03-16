-- Schema export for database: vacloudopsdb1
-- Generated: 2026-03-14 02:53:06
-- Tables: 135

-- -----------------------------------------------
-- Table: account_emailaddress
-- -----------------------------------------------
CREATE TABLE "account_emailaddress" (
    "id" integer NOT NULL,
    "email" character varying(254) NOT NULL,
    "verified" boolean NOT NULL,
    "primary" boolean NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "account_emailaddress" ADD CONSTRAINT "account_emailaddress_user_id_2c513194_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "account_emailaddress" ADD CONSTRAINT "account_emailaddress_pkey" PRIMARY KEY ("id");
ALTER TABLE "account_emailaddress" ADD CONSTRAINT "account_emailaddress_user_id_email_987c8728_uniq" UNIQUE ("user_id", "email");
ALTER TABLE "account_emailaddress" ADD CONSTRAINT "account_emailaddress_user_id_email_987c8728_uniq" UNIQUE ("user_id", "email");

CREATE INDEX account_emailaddress_email_03be32b2 ON public.account_emailaddress USING btree (email);
CREATE INDEX account_emailaddress_email_03be32b2_like ON public.account_emailaddress USING btree (email varchar_pattern_ops);
CREATE INDEX account_emailaddress_user_id_2c513194 ON public.account_emailaddress USING btree (user_id);
CREATE UNIQUE INDEX account_emailaddress_user_id_email_987c8728_uniq ON public.account_emailaddress USING btree (user_id, email);
CREATE UNIQUE INDEX unique_primary_email ON public.account_emailaddress USING btree (user_id, "primary") WHERE "primary";
CREATE UNIQUE INDEX unique_verified_email ON public.account_emailaddress USING btree (email) WHERE verified;

-- -----------------------------------------------
-- Table: account_emailconfirmation
-- -----------------------------------------------
CREATE TABLE "account_emailconfirmation" (
    "id" integer NOT NULL,
    "created" timestamp with time zone NOT NULL,
    "sent" timestamp with time zone,
    "key" character varying(64) NOT NULL,
    "email_address_id" integer NOT NULL
);

ALTER TABLE "account_emailconfirmation" ADD CONSTRAINT "account_emailconfirm_email_address_id_5b7f8c58_fk_account_e" FOREIGN KEY ("email_address_id") REFERENCES "account_emailaddress" ("id");
ALTER TABLE "account_emailconfirmation" ADD CONSTRAINT "account_emailconfirmation_pkey" PRIMARY KEY ("id");
ALTER TABLE "account_emailconfirmation" ADD CONSTRAINT "account_emailconfirmation_key_key" UNIQUE ("key");

CREATE INDEX account_emailconfirmation_email_address_id_5b7f8c58 ON public.account_emailconfirmation USING btree (email_address_id);
CREATE INDEX account_emailconfirmation_key_f43612bd_like ON public.account_emailconfirmation USING btree (key varchar_pattern_ops);
CREATE UNIQUE INDEX account_emailconfirmation_key_key ON public.account_emailconfirmation USING btree (key);

-- -----------------------------------------------
-- Table: agent_context
-- -----------------------------------------------
CREATE TABLE "agent_context" (
    "id" uuid NOT NULL,
    "context_type" character varying(100) NOT NULL,
    "context_data" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "session_id" uuid NOT NULL
);

ALTER TABLE "agent_context" ADD CONSTRAINT "agent_context_session_id_9009facf_fk_infrastru" FOREIGN KEY ("session_id") REFERENCES "infrastructure_agentsession" ("id");
ALTER TABLE "agent_context" ADD CONSTRAINT "agent_context_pkey" PRIMARY KEY ("id");
ALTER TABLE "agent_context" ADD CONSTRAINT "agent_context_session_id_context_type_20ef8e63_uniq" UNIQUE ("session_id", "context_type");
ALTER TABLE "agent_context" ADD CONSTRAINT "agent_context_session_id_context_type_20ef8e63_uniq" UNIQUE ("session_id", "context_type");

CREATE INDEX agent_conte_session_198e25_idx ON public.agent_context USING btree (session_id, context_type);
CREATE INDEX agent_conte_updated_84da42_idx ON public.agent_context USING btree (updated_at);
CREATE INDEX agent_context_session_id_9009facf ON public.agent_context USING btree (session_id);
CREATE UNIQUE INDEX agent_context_session_id_context_type_20ef8e63_uniq ON public.agent_context USING btree (session_id, context_type);
CREATE INDEX agent_context_updated_at_dd8ba7c9 ON public.agent_context USING btree (updated_at);

-- -----------------------------------------------
-- Table: agent_conversations
-- -----------------------------------------------
CREATE TABLE "agent_conversations" (
    "id" bigint NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "message_type" character varying(50) NOT NULL,
    "content" text NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL
);

ALTER TABLE "agent_conversations" ADD CONSTRAINT "agent_conversations_pkey" PRIMARY KEY ("id");

CREATE INDEX agent_conve_session_c55e97_idx ON public.agent_conversations USING btree (session_id, created_at);
CREATE INDEX agent_conversations_created_at_c7bae466 ON public.agent_conversations USING btree (created_at);
CREATE INDEX agent_conversations_session_id_6dc3d4d0 ON public.agent_conversations USING btree (session_id);
CREATE INDEX agent_conversations_session_id_6dc3d4d0_like ON public.agent_conversations USING btree (session_id varchar_pattern_ops);
CREATE INDEX idx_agent_conv_session ON public.agent_conversations USING btree (session_id);

-- -----------------------------------------------
-- Table: agent_definitions
-- -----------------------------------------------
CREATE TABLE "agent_definitions" (
    "id" uuid NOT NULL,
    "agent_id" character varying(100) NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text,
    "agent_type" character varying(50) NOT NULL,
    "default_model_id" character varying(255),
    "capabilities" jsonb NOT NULL,
    "endpoint_path" character varying(255),
    "mcp_servers" jsonb NOT NULL,
    "is_system" boolean NOT NULL,
    "is_active" boolean NOT NULL,
    "tenant_id" uuid,
    "workspace_id" uuid,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb
);

ALTER TABLE "agent_definitions" ADD CONSTRAINT "agent_definitions_pkey" PRIMARY KEY ("id");
ALTER TABLE "agent_definitions" ADD CONSTRAINT "agent_definitions_agent_id_key" UNIQUE ("agent_id");

CREATE INDEX agent_defin_is_acti_77fbea_idx ON public.agent_definitions USING btree (is_active);
CREATE INDEX agent_defin_tenant__0be7eb_idx ON public.agent_definitions USING btree (tenant_id);
CREATE INDEX agent_definitions_agent_id_ac7de3ab_like ON public.agent_definitions USING btree (agent_id varchar_pattern_ops);
CREATE UNIQUE INDEX agent_definitions_agent_id_key ON public.agent_definitions USING btree (agent_id);
CREATE INDEX agent_definitions_agent_type_1cd89b54 ON public.agent_definitions USING btree (agent_type);
CREATE INDEX agent_definitions_agent_type_1cd89b54_like ON public.agent_definitions USING btree (agent_type varchar_pattern_ops);
CREATE INDEX agent_definitions_is_active_f3d02ff2 ON public.agent_definitions USING btree (is_active);

-- -----------------------------------------------
-- Table: ai_model_registry
-- -----------------------------------------------
CREATE TABLE "ai_model_registry" (
    "id" uuid NOT NULL,
    "model_id" character varying(255) NOT NULL,
    "name" character varying(255) NOT NULL,
    "provider" character varying(50) NOT NULL,
    "model_type" character varying(50) NOT NULL,
    "capabilities" jsonb NOT NULL,
    "max_context_tokens" integer,
    "max_output_tokens" integer,
    "cost_per_1k_input" double precision,
    "cost_per_1k_output" double precision,
    "api_base_url" character varying(500),
    "supports_streaming" boolean NOT NULL,
    "is_active" boolean NOT NULL,
    "owner_user_id" uuid,
    "workspace_id" uuid,
    "tenant_id" uuid,
    "tenant_slug" character varying(100),
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb
);

ALTER TABLE "ai_model_registry" ADD CONSTRAINT "ai_model_registry_pkey" PRIMARY KEY ("id");
ALTER TABLE "ai_model_registry" ADD CONSTRAINT "ai_model_registry_model_id_key" UNIQUE ("model_id");

CREATE INDEX ai_model_re_is_acti_7a24b6_idx ON public.ai_model_registry USING btree (is_active);
CREATE INDEX ai_model_re_tenant__3dac75_idx ON public.ai_model_registry USING btree (tenant_id);
CREATE INDEX ai_model_registry_is_active_ff69ebfd ON public.ai_model_registry USING btree (is_active);
CREATE INDEX ai_model_registry_model_id_62e75dc8_like ON public.ai_model_registry USING btree (model_id varchar_pattern_ops);
CREATE UNIQUE INDEX ai_model_registry_model_id_key ON public.ai_model_registry USING btree (model_id);
CREATE INDEX ai_model_registry_model_type_9fe67bb6 ON public.ai_model_registry USING btree (model_type);
CREATE INDEX ai_model_registry_model_type_9fe67bb6_like ON public.ai_model_registry USING btree (model_type varchar_pattern_ops);
CREATE INDEX ai_model_registry_provider_835dd079 ON public.ai_model_registry USING btree (provider);
CREATE INDEX ai_model_registry_provider_835dd079_like ON public.ai_model_registry USING btree (provider varchar_pattern_ops);
CREATE INDEX ai_model_registry_tenant_slug_6b7d5956 ON public.ai_model_registry USING btree (tenant_slug);
CREATE INDEX ai_model_registry_tenant_slug_6b7d5956_like ON public.ai_model_registry USING btree (tenant_slug varchar_pattern_ops);

-- -----------------------------------------------
-- Table: auth_group
-- -----------------------------------------------
CREATE TABLE "auth_group" (
    "id" integer NOT NULL,
    "name" character varying(150) NOT NULL
);

ALTER TABLE "auth_group" ADD CONSTRAINT "auth_group_pkey" PRIMARY KEY ("id");
ALTER TABLE "auth_group" ADD CONSTRAINT "auth_group_name_key" UNIQUE ("name");

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);
CREATE UNIQUE INDEX auth_group_name_key ON public.auth_group USING btree (name);

-- -----------------------------------------------
-- Table: auth_group_permissions
-- -----------------------------------------------
CREATE TABLE "auth_group_permissions" (
    "id" bigint NOT NULL,
    "group_id" integer NOT NULL,
    "permission_id" integer NOT NULL
);

ALTER TABLE "auth_group_permissions" ADD CONSTRAINT "auth_group_permissio_permission_id_84c5c92e_fk_auth_perm" FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id");
ALTER TABLE "auth_group_permissions" ADD CONSTRAINT "auth_group_permissions_group_id_b120cbf9_fk_auth_group_id" FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id");
ALTER TABLE "auth_group_permissions" ADD CONSTRAINT "auth_group_permissions_pkey" PRIMARY KEY ("id");
ALTER TABLE "auth_group_permissions" ADD CONSTRAINT "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" UNIQUE ("group_id", "permission_id");
ALTER TABLE "auth_group_permissions" ADD CONSTRAINT "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" UNIQUE ("group_id", "permission_id");

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);
CREATE UNIQUE INDEX auth_group_permissions_group_id_permission_id_0cd325b0_uniq ON public.auth_group_permissions USING btree (group_id, permission_id);
CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);

-- -----------------------------------------------
-- Table: auth_permission
-- -----------------------------------------------
CREATE TABLE "auth_permission" (
    "id" integer NOT NULL,
    "name" character varying(255) NOT NULL,
    "content_type_id" integer NOT NULL,
    "codename" character varying(100) NOT NULL
);

ALTER TABLE "auth_permission" ADD CONSTRAINT "auth_permission_content_type_id_2f476e4b_fk_django_co" FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id");
ALTER TABLE "auth_permission" ADD CONSTRAINT "auth_permission_pkey" PRIMARY KEY ("id");
ALTER TABLE "auth_permission" ADD CONSTRAINT "auth_permission_content_type_id_codename_01ab375a_uniq" UNIQUE ("content_type_id", "codename");
ALTER TABLE "auth_permission" ADD CONSTRAINT "auth_permission_content_type_id_codename_01ab375a_uniq" UNIQUE ("content_type_id", "codename");

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);
CREATE UNIQUE INDEX auth_permission_content_type_id_codename_01ab375a_uniq ON public.auth_permission USING btree (content_type_id, codename);

-- -----------------------------------------------
-- Table: builds
-- -----------------------------------------------
CREATE TABLE "builds" (
    "id" uuid NOT NULL,
    "commit_sha" character varying(40) NOT NULL,
    "commit_message" text NOT NULL,
    "commit_author" character varying(255) NOT NULL,
    "branch" character varying(255) NOT NULL,
    "status" character varying(50) NOT NULL,
    "build_started_at" timestamp with time zone,
    "build_completed_at" timestamp with time zone,
    "build_duration" integer,
    "logs_url" character varying(500) NOT NULL,
    "artifacts_url" character varying(500) NOT NULL,
    "error_message" text NOT NULL,
    "error_details" jsonb NOT NULL,
    "build_number" integer NOT NULL,
    "triggered_by" character varying(50) NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "pipeline_id" uuid NOT NULL
);

ALTER TABLE "builds" ADD CONSTRAINT "builds_pipeline_id_22984bdc_fk_pipelines_id" FOREIGN KEY ("pipeline_id") REFERENCES "pipelines" ("id");
ALTER TABLE "builds" ADD CONSTRAINT "builds_pkey" PRIMARY KEY ("id");

CREATE INDEX builds_branch_58bd1426 ON public.builds USING btree (branch);
CREATE INDEX builds_branch_58bd1426_like ON public.builds USING btree (branch varchar_pattern_ops);
CREATE INDEX builds_build_s_8faa1f_idx ON public.builds USING btree (build_started_at);
CREATE INDEX builds_commit__eb12be_idx ON public.builds USING btree (commit_sha);
CREATE INDEX builds_commit_sha_03b57c44 ON public.builds USING btree (commit_sha);
CREATE INDEX builds_commit_sha_03b57c44_like ON public.builds USING btree (commit_sha varchar_pattern_ops);
CREATE INDEX builds_created_at_01cfa865 ON public.builds USING btree (created_at);
CREATE INDEX builds_pipelin_322a1b_idx ON public.builds USING btree (pipeline_id, status);
CREATE INDEX builds_pipeline_id_22984bdc ON public.builds USING btree (pipeline_id);
CREATE INDEX builds_status_77d2967e ON public.builds USING btree (status);
CREATE INDEX builds_status_77d2967e_like ON public.builds USING btree (status varchar_pattern_ops);

-- -----------------------------------------------
-- Table: campaign
-- -----------------------------------------------
CREATE TABLE "campaign" (
    "id" integer NOT NULL,
    "campaign_name" character varying(255) NOT NULL,
    "campaign_industry" character varying(100),
    "sales_representative" character varying(255) NOT NULL,
    "status" character varying(50) NOT NULL,
    "total_recipients" integer NOT NULL,
    "emails_sent" integer NOT NULL,
    "emails_failed" integer NOT NULL,
    "emails_clicked" integer NOT NULL,
    "emails_replied" integer NOT NULL,
    "template_path" character varying(500),
    "subject_line" text,
    "message_body" text,
    "provider" character varying(100),
    "origin" character varying(50) NOT NULL,
    "filter_city" character varying(100),
    "filter_state" character varying(100),
    "filter_lead_quality" character varying(20),
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "notes" text NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb,
    "sales_rep_id" integer
);

ALTER TABLE "campaign" ADD CONSTRAINT "campaign_sales_rep_id_b6e8ced8_fk_sales_representatives_id" FOREIGN KEY ("sales_rep_id") REFERENCES "sales_representatives" ("id");
ALTER TABLE "campaign" ADD CONSTRAINT "campaign_pkey" PRIMARY KEY ("id");
ALTER TABLE "campaign" ADD CONSTRAINT "campaign_campaign_name_created_at_ec7731de_uniq" UNIQUE ("campaign_name", "created_at");
ALTER TABLE "campaign" ADD CONSTRAINT "campaign_campaign_name_created_at_ec7731de_uniq" UNIQUE ("campaign_name", "created_at");

CREATE UNIQUE INDEX campaign_campaign_name_created_at_ec7731de_uniq ON public.campaign USING btree (campaign_name, created_at);
CREATE INDEX campaign_sales_rep_id_b6e8ced8 ON public.campaign USING btree (sales_rep_id);
CREATE INDEX idx_campaign_created_at ON public.campaign USING btree (created_at);
CREATE INDEX idx_campaign_name ON public.campaign USING btree (campaign_name);
CREATE INDEX idx_campaign_status ON public.campaign USING btree (status);

-- -----------------------------------------------
-- Table: chat_room_participants
-- -----------------------------------------------
CREATE TABLE "chat_room_participants" (
    "id" uuid NOT NULL,
    "role" character varying(20) NOT NULL,
    "is_muted" boolean NOT NULL,
    "is_banned" boolean NOT NULL,
    "mute_until" timestamp with time zone,
    "can_mention_all" boolean NOT NULL,
    "joined_at" timestamp with time zone NOT NULL,
    "last_seen" timestamp with time zone NOT NULL,
    "message_count" integer NOT NULL,
    "notifications_enabled" boolean NOT NULL,
    "mention_notifications" boolean NOT NULL,
    "notification_settings" jsonb,
    "room_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "chat_room_participants" ADD CONSTRAINT "chat_room_participants_room_id_95ffc97d_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "chat_room_participants" ADD CONSTRAINT "chat_room_participants_user_id_e1e48324_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "chat_room_participants" ADD CONSTRAINT "chat_room_participants_pkey" PRIMARY KEY ("id");
ALTER TABLE "chat_room_participants" ADD CONSTRAINT "chat_room_participants_room_id_user_id_63c6cee2_uniq" UNIQUE ("room_id", "user_id");
ALTER TABLE "chat_room_participants" ADD CONSTRAINT "chat_room_participants_room_id_user_id_63c6cee2_uniq" UNIQUE ("room_id", "user_id");

CREATE INDEX chat_room_p_room_id_6f9ec7_idx ON public.chat_room_participants USING btree (room_id, role);
CREATE INDEX chat_room_p_user_id_b4f22c_idx ON public.chat_room_participants USING btree (user_id, is_banned);
CREATE INDEX chat_room_participants_room_id_95ffc97d ON public.chat_room_participants USING btree (room_id);
CREATE UNIQUE INDEX chat_room_participants_room_id_user_id_63c6cee2_uniq ON public.chat_room_participants USING btree (room_id, user_id);
CREATE INDEX chat_room_participants_user_id_e1e48324 ON public.chat_room_participants USING btree (user_id);

-- -----------------------------------------------
-- Table: chat_rooms
-- -----------------------------------------------
CREATE TABLE "chat_rooms" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text,
    "room_type" character varying(20) NOT NULL,
    "required_subscription_level" character varying(20) NOT NULL,
    "max_participants" integer NOT NULL,
    "is_active" boolean NOT NULL,
    "is_public" boolean NOT NULL,
    "file_sharing_enabled" boolean NOT NULL,
    "moderated" boolean NOT NULL,
    "slow_mode_seconds" integer NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "last_activity" timestamp with time zone NOT NULL,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "settings" jsonb,
    "created_by_id" bigint NOT NULL,
    "organization_id" uuid NOT NULL
);

ALTER TABLE "chat_rooms" ADD CONSTRAINT "chat_rooms_created_by_id_b5269f8f_fk_users_user_id" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "chat_rooms" ADD CONSTRAINT "chat_rooms_organization_id_c405766a_fk_users_organization_id" FOREIGN KEY ("organization_id") REFERENCES "users_organization" ("id");
ALTER TABLE "chat_rooms" ADD CONSTRAINT "chat_rooms_pkey" PRIMARY KEY ("id");

CREATE INDEX chat_rooms_created_by_id_b5269f8f ON public.chat_rooms USING btree (created_by_id);
CREATE INDEX chat_rooms_is_acti_bf4934_idx ON public.chat_rooms USING btree (is_active, is_public);
CREATE INDEX chat_rooms_organiz_f8b89f_idx ON public.chat_rooms USING btree (organization_id, room_type);
CREATE INDEX chat_rooms_organization_id_c405766a ON public.chat_rooms USING btree (organization_id);

-- -----------------------------------------------
-- Table: cloud_conversation_history
-- -----------------------------------------------
CREATE TABLE "cloud_conversation_history" (
    "id" bigint NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "message_type" character varying(50) NOT NULL,
    "content" text NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL DEFAULT now()
);

ALTER TABLE "cloud_conversation_history" ADD CONSTRAINT "cloud_conversation_history_pkey" PRIMARY KEY ("id");

CREATE INDEX cloud_conve_session_38d2f3_idx ON public.cloud_conversation_history USING btree (session_id, created_at);
CREATE INDEX cloud_conversation_history_created_at_fa707dde ON public.cloud_conversation_history USING btree (created_at);
CREATE INDEX cloud_conversation_history_session_id_4a2e10fb ON public.cloud_conversation_history USING btree (session_id);
CREATE INDEX cloud_conversation_history_session_id_4a2e10fb_like ON public.cloud_conversation_history USING btree (session_id varchar_pattern_ops);
CREATE INDEX idx_cloud_conv_session ON public.cloud_conversation_history USING btree (session_id);
CREATE INDEX idx_cloud_conv_session_created ON public.cloud_conversation_history USING btree (session_id, created_at);

-- -----------------------------------------------
-- Table: cloud_cost_tracking
-- -----------------------------------------------
CREATE TABLE "cloud_cost_tracking" (
    "id" bigint NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "resource_id" character varying(255) NOT NULL,
    "provider" character varying(50) NOT NULL,
    "resource_type" character varying(100) NOT NULL,
    "estimated_cost" numeric(10,2),
    "actual_cost" numeric(10,2),
    "cost_period" character varying(20) NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL
);

ALTER TABLE "cloud_cost_tracking" ADD CONSTRAINT "cloud_cost_tracking_pkey" PRIMARY KEY ("id");
ALTER TABLE "cloud_cost_tracking" ADD CONSTRAINT "cloud_cost_tracking_session_id_resource_id_b49a0ce9_uniq" UNIQUE ("session_id", "resource_id");
ALTER TABLE "cloud_cost_tracking" ADD CONSTRAINT "cloud_cost_tracking_session_id_resource_id_b49a0ce9_uniq" UNIQUE ("session_id", "resource_id");

CREATE INDEX cloud_cost__resourc_903cff_idx ON public.cloud_cost_tracking USING btree (resource_type);
CREATE INDEX cloud_cost__session_a26c1f_idx ON public.cloud_cost_tracking USING btree (session_id, provider);
CREATE INDEX cloud_cost_tracking_created_at_1e7091b5 ON public.cloud_cost_tracking USING btree (created_at);
CREATE INDEX cloud_cost_tracking_session_id_22b0bae0 ON public.cloud_cost_tracking USING btree (session_id);
CREATE INDEX cloud_cost_tracking_session_id_22b0bae0_like ON public.cloud_cost_tracking USING btree (session_id varchar_pattern_ops);
CREATE UNIQUE INDEX cloud_cost_tracking_session_id_resource_id_b49a0ce9_uniq ON public.cloud_cost_tracking USING btree (session_id, resource_id);
CREATE INDEX idx_cloud_cost_resource_type ON public.cloud_cost_tracking USING btree (resource_type);
CREATE INDEX idx_cloud_cost_session_provider ON public.cloud_cost_tracking USING btree (session_id, provider);

-- -----------------------------------------------
-- Table: cloud_deployment_history
-- -----------------------------------------------
CREATE TABLE "cloud_deployment_history" (
    "id" bigint NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "deployment_id" character varying(255) NOT NULL,
    "solution_id" character varying(255) NOT NULL,
    "provider" character varying(50) NOT NULL,
    "status" character varying(50) NOT NULL,
    "deployment_config" jsonb NOT NULL,
    "logs" text NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "completed_at" timestamp with time zone
);

ALTER TABLE "cloud_deployment_history" ADD CONSTRAINT "cloud_deployment_history_pkey" PRIMARY KEY ("id");
ALTER TABLE "cloud_deployment_history" ADD CONSTRAINT "cloud_deployment_history_deployment_id_key" UNIQUE ("deployment_id");

CREATE INDEX cloud_deplo_deploym_a9303b_idx ON public.cloud_deployment_history USING btree (deployment_id);
CREATE INDEX cloud_deplo_session_7f0925_idx ON public.cloud_deployment_history USING btree (session_id, status);
CREATE INDEX cloud_deployment_history_created_at_b3646401 ON public.cloud_deployment_history USING btree (created_at);
CREATE INDEX cloud_deployment_history_deployment_id_7f127022_like ON public.cloud_deployment_history USING btree (deployment_id varchar_pattern_ops);
CREATE UNIQUE INDEX cloud_deployment_history_deployment_id_key ON public.cloud_deployment_history USING btree (deployment_id);
CREATE INDEX cloud_deployment_history_session_id_b8fcf26f ON public.cloud_deployment_history USING btree (session_id);
CREATE INDEX cloud_deployment_history_session_id_b8fcf26f_like ON public.cloud_deployment_history USING btree (session_id varchar_pattern_ops);
CREATE INDEX idx_cloud_deployment_deployment_id ON public.cloud_deployment_history USING btree (deployment_id);
CREATE INDEX idx_cloud_deployment_session_status ON public.cloud_deployment_history USING btree (session_id, status);

-- -----------------------------------------------
-- Table: cloud_solutions
-- -----------------------------------------------
CREATE TABLE "cloud_solutions" (
    "id" bigint NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "solution_id" character varying(255) NOT NULL,
    "provider" character varying(50) NOT NULL,
    "solution_type" character varying(100),
    "solution_code" text NOT NULL,
    "description" text NOT NULL,
    "tags" jsonb NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL
);

ALTER TABLE "cloud_solutions" ADD CONSTRAINT "cloud_solutions_pkey" PRIMARY KEY ("id");
ALTER TABLE "cloud_solutions" ADD CONSTRAINT "cloud_solutions_solution_id_key" UNIQUE ("solution_id");

CREATE INDEX cloud_solut_session_6972d5_idx ON public.cloud_solutions USING btree (session_id, provider);
CREATE INDEX cloud_solut_solutio_3ac5b4_idx ON public.cloud_solutions USING btree (solution_id);
CREATE INDEX cloud_solutions_created_at_65834198 ON public.cloud_solutions USING btree (created_at);
CREATE INDEX cloud_solutions_session_id_b6b1334c ON public.cloud_solutions USING btree (session_id);
CREATE INDEX cloud_solutions_session_id_b6b1334c_like ON public.cloud_solutions USING btree (session_id varchar_pattern_ops);
CREATE INDEX cloud_solutions_solution_id_e86f71ed_like ON public.cloud_solutions USING btree (solution_id varchar_pattern_ops);
CREATE UNIQUE INDEX cloud_solutions_solution_id_key ON public.cloud_solutions USING btree (solution_id);
CREATE INDEX idx_cloud_solutions_description_fts ON public.cloud_solutions USING gin (to_tsvector('english'::regconfig, ((description || ' '::text) || solution_code)));
CREATE INDEX idx_cloud_solutions_session_provider ON public.cloud_solutions USING btree (session_id, provider);
CREATE INDEX idx_cloud_solutions_solution_id ON public.cloud_solutions USING btree (solution_id);

-- -----------------------------------------------
-- Table: code_snippets
-- -----------------------------------------------
CREATE TABLE "code_snippets" (
    "id" uuid NOT NULL,
    "language" character varying(50) NOT NULL,
    "code" text NOT NULL,
    "description" text NOT NULL,
    "tags" jsonb NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "session_id" uuid NOT NULL
);

ALTER TABLE "code_snippets" ADD CONSTRAINT "code_snippets_session_id_7cb920a1_fk_infrastru" FOREIGN KEY ("session_id") REFERENCES "infrastructure_agentsession" ("id");
ALTER TABLE "code_snippets" ADD CONSTRAINT "code_snippets_pkey" PRIMARY KEY ("id");

CREATE INDEX code_snippe_languag_a69d11_idx ON public.code_snippets USING btree (language, created_at);
CREATE INDEX code_snippe_session_7c0ef1_idx ON public.code_snippets USING btree (session_id, language);
CREATE INDEX code_snippets_created_at_75f80088 ON public.code_snippets USING btree (created_at);
CREATE INDEX code_snippets_session_id_7cb920a1 ON public.code_snippets USING btree (session_id);

-- -----------------------------------------------
-- Table: data_browser_view
-- -----------------------------------------------
CREATE TABLE "data_browser_view" (
    "id" character varying(12) NOT NULL,
    "created_time" timestamp with time zone NOT NULL,
    "name" character varying(64) NOT NULL,
    "description" text NOT NULL,
    "public" boolean NOT NULL,
    "model_name" character varying(64) NOT NULL,
    "fields" text NOT NULL,
    "query" text NOT NULL,
    "owner_id" bigint,
    "public_slug" character varying(12) NOT NULL,
    "limit" integer NOT NULL,
    "shared" boolean NOT NULL,
    "folder" character varying(64) NOT NULL
);

ALTER TABLE "data_browser_view" ADD CONSTRAINT "data_browser_view_owner_id_2851e901_fk_users_user_id" FOREIGN KEY ("owner_id") REFERENCES "users_user" ("id");
ALTER TABLE "data_browser_view" ADD CONSTRAINT "data_browser_view_pkey" PRIMARY KEY ("id");

CREATE INDEX data_browser_view_owner_id_2851e901 ON public.data_browser_view USING btree (owner_id);

-- -----------------------------------------------
-- Table: deployments
-- -----------------------------------------------
CREATE TABLE "deployments" (
    "id" uuid NOT NULL,
    "environment" character varying(50) NOT NULL,
    "status" character varying(50) NOT NULL,
    "deployment_target" character varying(100) NOT NULL,
    "target_resource_id" character varying(255) NOT NULL,
    "deployment_url" character varying(500) NOT NULL,
    "deployment_config" jsonb NOT NULL,
    "deployment_logs" text NOT NULL,
    "error_message" text NOT NULL,
    "deployed_at" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "build_id" uuid NOT NULL,
    "pipeline_id" uuid NOT NULL
);

ALTER TABLE "deployments" ADD CONSTRAINT "deployments_build_id_2aaed76d_fk_builds_id" FOREIGN KEY ("build_id") REFERENCES "builds" ("id");
ALTER TABLE "deployments" ADD CONSTRAINT "deployments_pipeline_id_df569848_fk_pipelines_id" FOREIGN KEY ("pipeline_id") REFERENCES "pipelines" ("id");
ALTER TABLE "deployments" ADD CONSTRAINT "deployments_pkey" PRIMARY KEY ("id");

CREATE INDEX deployments_build_i_2559ff_idx ON public.deployments USING btree (build_id, status);
CREATE INDEX deployments_build_id_2aaed76d ON public.deployments USING btree (build_id);
CREATE INDEX deployments_created_at_18a25bc3 ON public.deployments USING btree (created_at);
CREATE INDEX deployments_deploye_6eed1f_idx ON public.deployments USING btree (deployed_at);
CREATE INDEX deployments_pipelin_47884d_idx ON public.deployments USING btree (pipeline_id, environment, status);
CREATE INDEX deployments_pipeline_id_df569848 ON public.deployments USING btree (pipeline_id);
CREATE INDEX deployments_status_207e4806 ON public.deployments USING btree (status);
CREATE INDEX deployments_status_207e4806_like ON public.deployments USING btree (status varchar_pattern_ops);

-- -----------------------------------------------
-- Table: django_admin_log
-- -----------------------------------------------
CREATE TABLE "django_admin_log" (
    "id" integer NOT NULL,
    "action_time" timestamp with time zone NOT NULL,
    "object_id" text,
    "object_repr" character varying(200) NOT NULL,
    "action_flag" smallint NOT NULL,
    "change_message" text NOT NULL,
    "content_type_id" integer,
    "user_id" bigint NOT NULL
);

ALTER TABLE "django_admin_log" ADD CONSTRAINT "django_admin_log_content_type_id_c4bce8eb_fk_django_co" FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id");
ALTER TABLE "django_admin_log" ADD CONSTRAINT "django_admin_log_user_id_c564eba6_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "django_admin_log" ADD CONSTRAINT "django_admin_log_pkey" PRIMARY KEY ("id");

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);
CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);

-- -----------------------------------------------
-- Table: django_content_type
-- -----------------------------------------------
CREATE TABLE "django_content_type" (
    "id" integer NOT NULL,
    "app_label" character varying(100) NOT NULL,
    "model" character varying(100) NOT NULL
);

ALTER TABLE "django_content_type" ADD CONSTRAINT "django_content_type_pkey" PRIMARY KEY ("id");
ALTER TABLE "django_content_type" ADD CONSTRAINT "django_content_type_app_label_model_76bd3d3b_uniq" UNIQUE ("app_label", "model");
ALTER TABLE "django_content_type" ADD CONSTRAINT "django_content_type_app_label_model_76bd3d3b_uniq" UNIQUE ("app_label", "model");

CREATE UNIQUE INDEX django_content_type_app_label_model_76bd3d3b_uniq ON public.django_content_type USING btree (app_label, model);

-- -----------------------------------------------
-- Table: django_migrations
-- -----------------------------------------------
CREATE TABLE "django_migrations" (
    "id" bigint NOT NULL,
    "app" character varying(255) NOT NULL,
    "name" character varying(255) NOT NULL,
    "applied" timestamp with time zone NOT NULL
);

ALTER TABLE "django_migrations" ADD CONSTRAINT "django_migrations_pkey" PRIMARY KEY ("id");

-- -----------------------------------------------
-- Table: django_session
-- -----------------------------------------------
CREATE TABLE "django_session" (
    "session_key" character varying(40) NOT NULL,
    "session_data" text NOT NULL,
    "expire_date" timestamp with time zone NOT NULL
);

ALTER TABLE "django_session" ADD CONSTRAINT "django_session_pkey" PRIMARY KEY ("session_key");

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);
CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);

-- -----------------------------------------------
-- Table: evals
-- -----------------------------------------------
CREATE TABLE "evals" (
    "id" character varying NOT NULL,
    "request_id" character varying NOT NULL,
    "model_id" character varying NOT NULL,
    "tenant_id" character varying NOT NULL,
    "feedback_type" feedbacktype NOT NULL,
    "feedback_value" integer,
    "feedback_text" text,
    "query" text,
    "response" text,
    "prompt" text,
    "eval_metadata" json,
    "response_time_ms" double precision,
    "token_count" integer,
    "reasoning_steps" integer,
    "created_at" timestamp with time zone DEFAULT now()
);

ALTER TABLE "evals" ADD CONSTRAINT "evals_model_id_fkey" FOREIGN KEY ("model_id") REFERENCES "models" ("id");
ALTER TABLE "evals" ADD CONSTRAINT "evals_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "tenants" ("id");
ALTER TABLE "evals" ADD CONSTRAINT "evals_pkey" PRIMARY KEY ("id");

CREATE INDEX ix_evals_id ON public.evals USING btree (id);
CREATE INDEX ix_evals_model_id ON public.evals USING btree (model_id);
CREATE INDEX ix_evals_request_id ON public.evals USING btree (request_id);
CREATE INDEX ix_evals_tenant_id ON public.evals USING btree (tenant_id);

-- -----------------------------------------------
-- Table: generic_records
-- -----------------------------------------------
CREATE TABLE "generic_records" (
    "id" uuid NOT NULL,
    "record_type" character varying(100),
    "slug" character varying(200),
    "label" character varying(500),
    "description" text,
    "tenant_id" uuid,
    "workspace_id" uuid,
    "user_id" uuid,
    "organization_id" uuid,
    "owner_user_id" uuid,
    "value_char" character varying(500),
    "value_char_long" character varying(2000),
    "value_text" text,
    "value_int" integer,
    "value_bigint" bigint,
    "value_float" double precision,
    "value_decimal" numeric(20,8),
    "value_bool" boolean,
    "value_date" date,
    "value_datetime" timestamp with time zone,
    "value_uuid" uuid,
    "value_url" character varying(2000),
    "value_email" character varying(254),
    "value_ip" inet,
    "value_duration_seconds" integer,
    "payload" jsonb NOT NULL,
    "metadata" jsonb NOT NULL,
    "schema_hint" character varying(255),
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "expires_at" timestamp with time zone,
    "is_active" boolean NOT NULL,
    "reserved_char_1" character varying(255),
    "reserved_char_2" character varying(255),
    "reserved_char_3" character varying(255),
    "reserved_char_4" character varying(255),
    "reserved_char_5" character varying(500),
    "reserved_text_1" text,
    "reserved_text_2" text,
    "reserved_int_1" integer,
    "reserved_int_2" integer,
    "reserved_int_3" integer,
    "reserved_bigint_1" bigint,
    "reserved_float_1" double precision,
    "reserved_float_2" double precision,
    "reserved_decimal_1" numeric(20,8),
    "reserved_bool_1" boolean,
    "reserved_bool_2" boolean,
    "reserved_bool_3" boolean,
    "reserved_bool_4" boolean,
    "reserved_bool_5" boolean,
    "reserved_date_1" date,
    "reserved_datetime_1" timestamp with time zone,
    "reserved_datetime_2" timestamp with time zone,
    "reserved_uuid_1" uuid,
    "reserved_uuid_2" uuid,
    "reserved_url_1" character varying(2000),
    "reserved_email_1" character varying(254),
    "reserved_json_1" jsonb,
    "reserved_json_2" jsonb,
    "reserved_json_3" jsonb,
    "reserved_json_4" jsonb,
    "reserved_json_5" jsonb,
    "reserved_json_6" jsonb,
    "reserved_json_7" jsonb,
    "reserved_json_8" jsonb,
    "reserved_json_9" jsonb,
    "reserved_json_10" jsonb,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb
);

ALTER TABLE "generic_records" ADD CONSTRAINT "generic_records_pkey" PRIMARY KEY ("id");

CREATE INDEX generic_rec_is_acti_eeff23_idx ON public.generic_records USING btree (is_active);
CREATE INDEX generic_rec_record__7e67da_idx ON public.generic_records USING btree (record_type, created_at);
CREATE INDEX generic_rec_slug_9df00a_idx ON public.generic_records USING btree (slug);
CREATE INDEX generic_rec_tenant__ff3f08_idx ON public.generic_records USING btree (tenant_id, record_type);
CREATE INDEX generic_records_created_at_f06df36f ON public.generic_records USING btree (created_at);
CREATE INDEX generic_records_is_active_b1ef098c ON public.generic_records USING btree (is_active);
CREATE INDEX generic_records_record_type_41ff248e ON public.generic_records USING btree (record_type);
CREATE INDEX generic_records_record_type_41ff248e_like ON public.generic_records USING btree (record_type varchar_pattern_ops);
CREATE INDEX generic_records_slug_4fcde5d9 ON public.generic_records USING btree (slug);
CREATE INDEX generic_records_slug_4fcde5d9_like ON public.generic_records USING btree (slug varchar_pattern_ops);
CREATE INDEX generic_records_tenant_id_bbda492e ON public.generic_records USING btree (tenant_id);
CREATE INDEX generic_records_user_id_56d4f350 ON public.generic_records USING btree (user_id);

-- -----------------------------------------------
-- Table: git_repositories
-- -----------------------------------------------
CREATE TABLE "git_repositories" (
    "id" uuid NOT NULL,
    "provider" character varying(50) NOT NULL,
    "repository_url" character varying(500) NOT NULL,
    "repository_id" character varying(255) NOT NULL,
    "repository_name" character varying(255) NOT NULL,
    "repository_owner" character varying(255) NOT NULL,
    "access_token_encrypted" text NOT NULL,
    "webhook_id" character varying(255) NOT NULL,
    "webhook_secret_encrypted" text NOT NULL,
    "webhook_url" character varying(500) NOT NULL,
    "default_branch" character varying(255) NOT NULL,
    "is_private" boolean NOT NULL,
    "is_active" boolean NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "git_repositories" ADD CONSTRAINT "git_repositories_user_id_91fd62ba_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "git_repositories" ADD CONSTRAINT "git_repositories_pkey" PRIMARY KEY ("id");
ALTER TABLE "git_repositories" ADD CONSTRAINT "git_repositories_user_id_provider_repository_id_5b7b83c7_uniq" UNIQUE ("user_id", "provider", "repository_id");
ALTER TABLE "git_repositories" ADD CONSTRAINT "git_repositories_user_id_provider_repository_id_5b7b83c7_uniq" UNIQUE ("user_id", "provider", "repository_id");
ALTER TABLE "git_repositories" ADD CONSTRAINT "git_repositories_user_id_provider_repository_id_5b7b83c7_uniq" UNIQUE ("user_id", "provider", "repository_id");

CREATE INDEX git_reposit_reposit_df8210_idx ON public.git_repositories USING btree (repository_id);
CREATE INDEX git_reposit_user_id_010af8_idx ON public.git_repositories USING btree (user_id, provider);
CREATE INDEX git_repositories_created_at_a9458803 ON public.git_repositories USING btree (created_at);
CREATE INDEX git_repositories_repository_id_dc150e22 ON public.git_repositories USING btree (repository_id);
CREATE INDEX git_repositories_repository_id_dc150e22_like ON public.git_repositories USING btree (repository_id varchar_pattern_ops);
CREATE INDEX git_repositories_user_id_91fd62ba ON public.git_repositories USING btree (user_id);
CREATE UNIQUE INDEX git_repositories_user_id_provider_repository_id_5b7b83c7_uniq ON public.git_repositories USING btree (user_id, provider, repository_id);

-- -----------------------------------------------
-- Table: infrastructure_agentsession
-- -----------------------------------------------
CREATE TABLE "infrastructure_agentsession" (
    "id" uuid NOT NULL,
    "session_token" character varying(255) NOT NULL,
    "session_type" character varying(30) NOT NULL,
    "status" character varying(20) NOT NULL,
    "agent_type" character varying(50) NOT NULL,
    "agent_version" character varying(50) NOT NULL,
    "agent_capabilities" jsonb NOT NULL,
    "session_state" jsonb NOT NULL,
    "context_memory" jsonb NOT NULL,
    "working_memory" jsonb NOT NULL,
    "allocated_resources" jsonb NOT NULL,
    "resource_limits" jsonb NOT NULL,
    "current_usage" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "last_activity" timestamp with time zone NOT NULL,
    "expires_at" timestamp with time zone,
    "total_requests" bigint NOT NULL,
    "successful_requests" bigint NOT NULL,
    "failed_requests" bigint NOT NULL,
    "average_response_time_ms" double precision,
    "websocket_connections" jsonb NOT NULL,
    "notification_preferences" jsonb NOT NULL,
    "real_time_enabled" boolean NOT NULL,
    "collaboration_sessions" jsonb NOT NULL,
    "handoff_history" jsonb NOT NULL,
    "active_conversations" jsonb NOT NULL,
    "mcp_servers" jsonb NOT NULL,
    "tool_usage" jsonb NOT NULL,
    "owner_user_id" uuid,
    "owner_username" character varying(150),
    "owner_email" character varying(254),
    "workspace_id" uuid,
    "workspace_name" character varying(255),
    "tenant_id" uuid,
    "tenant_name" character varying(255),
    "tenant_slug" character varying(100),
    "deployment_environment" character varying(50),
    "deployment_region" character varying(100),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "parent_session_id" uuid,
    "agent_config_id" uuid
);

ALTER TABLE "infrastructure_agentsession" ADD CONSTRAINT "infrastructure_agent_agent_config_id_21285c24_fk_infrastru" FOREIGN KEY ("agent_config_id") REFERENCES "infrastructure_aiagentconfiguration" ("id");
ALTER TABLE "infrastructure_agentsession" ADD CONSTRAINT "infrastructure_agent_parent_session_id_417c6f7b_fk_infrastru" FOREIGN KEY ("parent_session_id") REFERENCES "infrastructure_agentsession" ("id");
ALTER TABLE "infrastructure_agentsession" ADD CONSTRAINT "infrastructure_agentsession_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_agentsession" ADD CONSTRAINT "infrastructure_agentsession_session_token_key" UNIQUE ("session_token");

CREATE INDEX infrastruct_agent_t_39ff13_idx ON public.infrastructure_agentsession USING btree (agent_type);
CREATE INDEX infrastruct_expires_0b90bd_idx ON public.infrastructure_agentsession USING btree (expires_at);
CREATE INDEX infrastruct_last_ac_5c38a6_idx ON public.infrastructure_agentsession USING btree (last_activity);
CREATE INDEX infrastruct_owner_u_f0395e_idx ON public.infrastructure_agentsession USING btree (owner_user_id);
CREATE INDEX infrastruct_session_0e628e_idx ON public.infrastructure_agentsession USING btree (session_type);
CREATE INDEX infrastruct_session_df5777_idx ON public.infrastructure_agentsession USING btree (session_token);
CREATE INDEX infrastruct_status_16a6f0_idx ON public.infrastructure_agentsession USING btree (status);
CREATE INDEX infrastruct_tenant__357ea1_idx ON public.infrastructure_agentsession USING btree (tenant_id);
CREATE INDEX infrastruct_tenant__d00e27_idx ON public.infrastructure_agentsession USING btree (tenant_slug);
CREATE INDEX infrastruct_workspa_9472c3_idx ON public.infrastructure_agentsession USING btree (workspace_id);
CREATE INDEX infrastructure_agentsession_agent_config_id_21285c24 ON public.infrastructure_agentsession USING btree (agent_config_id);
CREATE INDEX infrastructure_agentsession_parent_session_id_417c6f7b ON public.infrastructure_agentsession USING btree (parent_session_id);
CREATE INDEX infrastructure_agentsession_session_token_28bbd839_like ON public.infrastructure_agentsession USING btree (session_token varchar_pattern_ops);
CREATE UNIQUE INDEX infrastructure_agentsession_session_token_key ON public.infrastructure_agentsession USING btree (session_token);
CREATE INDEX infrastructure_agentsession_tenant_slug_a5b11d3a ON public.infrastructure_agentsession USING btree (tenant_slug);
CREATE INDEX infrastructure_agentsession_tenant_slug_a5b11d3a_like ON public.infrastructure_agentsession USING btree (tenant_slug varchar_pattern_ops);

-- -----------------------------------------------
-- Table: infrastructure_aiagentconfiguration
-- -----------------------------------------------
CREATE TABLE "infrastructure_aiagentconfiguration" (
    "id" uuid NOT NULL,
    "config_key" character varying(255) NOT NULL,
    "config_value" jsonb NOT NULL,
    "config_type" character varying(50) NOT NULL,
    "scope" character varying(20) NOT NULL,
    "environment" character varying(20),
    "description" text,
    "version" character varying(20) NOT NULL,
    "schema_version" character varying(20) NOT NULL,
    "is_active" boolean NOT NULL,
    "is_encrypted" boolean NOT NULL,
    "is_readonly" boolean NOT NULL,
    "requires_restart" boolean NOT NULL,
    "validation_schema" jsonb,
    "constraints" jsonb,
    "default_value" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "effective_from" timestamp with time zone,
    "effective_until" timestamp with time zone,
    "last_applied" timestamp with time zone,
    "change_reason" text,
    "previous_value" jsonb,
    "rollback_available" boolean NOT NULL,
    "depends_on" jsonb NOT NULL,
    "affects" jsonb NOT NULL,
    "monitoring_enabled" boolean NOT NULL,
    "alert_on_change" boolean NOT NULL,
    "usage_tracking" boolean NOT NULL,
    "access_count" bigint NOT NULL,
    "last_accessed" timestamp with time zone,
    "access_level" character varying(20) NOT NULL,
    "allowed_roles" jsonb NOT NULL,
    "audit_trail" jsonb NOT NULL,
    "ai_model_provider" character varying(100),
    "ai_model_name" character varying(100),
    "ai_model_version" character varying(50),
    "cache_ttl_seconds" integer NOT NULL,
    "priority" integer NOT NULL,
    "resource_weight" double precision NOT NULL,
    "webhook_url" character varying(200),
    "external_sync" boolean NOT NULL,
    "sync_frequency" integer NOT NULL,
    "owner_user_id" uuid,
    "owner_username" character varying(150),
    "owner_email" character varying(254),
    "workspace_id" uuid,
    "workspace_name" character varying(255),
    "tenant_id" uuid,
    "tenant_name" character varying(255),
    "tenant_slug" character varying(100),
    "deployment_environment" character varying(50),
    "deployment_region" character varying(100),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "parent_config_id" uuid
);

ALTER TABLE "infrastructure_aiagentconfiguration" ADD CONSTRAINT "infrastructure_aiage_parent_config_id_530cadea_fk_infrastru" FOREIGN KEY ("parent_config_id") REFERENCES "infrastructure_aiagentconfiguration" ("id");
ALTER TABLE "infrastructure_aiagentconfiguration" ADD CONSTRAINT "infrastructure_aiagentconfiguration_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_aiagentconfiguration" ADD CONSTRAINT "unique_config_key_scope_environment" UNIQUE ("config_key", "scope", "environment");
ALTER TABLE "infrastructure_aiagentconfiguration" ADD CONSTRAINT "unique_config_key_scope_environment" UNIQUE ("config_key", "scope", "environment");
ALTER TABLE "infrastructure_aiagentconfiguration" ADD CONSTRAINT "unique_config_key_scope_environment" UNIQUE ("config_key", "scope", "environment");

CREATE INDEX infrastruct_config__3ad9b0_idx ON public.infrastructure_aiagentconfiguration USING btree (config_type);
CREATE INDEX infrastruct_config__cbf7f9_idx ON public.infrastructure_aiagentconfiguration USING btree (config_key);
CREATE INDEX infrastruct_effecti_532739_idx ON public.infrastructure_aiagentconfiguration USING btree (effective_from);
CREATE INDEX infrastruct_effecti_6532c8_idx ON public.infrastructure_aiagentconfiguration USING btree (effective_until);
CREATE INDEX infrastruct_environ_b5ed4a_idx ON public.infrastructure_aiagentconfiguration USING btree (environment);
CREATE INDEX infrastruct_is_acti_2c8c62_idx ON public.infrastructure_aiagentconfiguration USING btree (is_active);
CREATE INDEX infrastruct_last_ac_1f9095_idx ON public.infrastructure_aiagentconfiguration USING btree (last_accessed);
CREATE INDEX infrastruct_owner_u_edb1a3_idx ON public.infrastructure_aiagentconfiguration USING btree (owner_user_id);
CREATE INDEX infrastruct_priorit_f5539a_idx ON public.infrastructure_aiagentconfiguration USING btree (priority);
CREATE INDEX infrastruct_scope_92095a_idx ON public.infrastructure_aiagentconfiguration USING btree (scope);
CREATE INDEX infrastruct_tenant__ac10ff_idx ON public.infrastructure_aiagentconfiguration USING btree (tenant_id);
CREATE INDEX infrastruct_tenant__e80c3a_idx ON public.infrastructure_aiagentconfiguration USING btree (tenant_slug);
CREATE INDEX infrastruct_workspa_8fcde6_idx ON public.infrastructure_aiagentconfiguration USING btree (workspace_id);
CREATE INDEX infrastructure_aiagentconfiguration_parent_config_id_530cadea ON public.infrastructure_aiagentconfiguration USING btree (parent_config_id);
CREATE INDEX infrastructure_aiagentconfiguration_tenant_slug_afcac045 ON public.infrastructure_aiagentconfiguration USING btree (tenant_slug);
CREATE INDEX infrastructure_aiagentconfiguration_tenant_slug_afcac045_like ON public.infrastructure_aiagentconfiguration USING btree (tenant_slug varchar_pattern_ops);
CREATE UNIQUE INDEX unique_config_key_scope_environment ON public.infrastructure_aiagentconfiguration USING btree (config_key, scope, environment);

-- -----------------------------------------------
-- Table: infrastructure_aiagentquery
-- -----------------------------------------------
CREATE TABLE "infrastructure_aiagentquery" (
    "id" uuid NOT NULL,
    "session_id" uuid,
    "query_text" text NOT NULL,
    "query_type" character varying(50) NOT NULL,
    "intent_category" character varying(100),
    "priority" character varying(20) NOT NULL,
    "status" character varying(20) NOT NULL,
    "metadata" jsonb NOT NULL,
    "ai_confidence_score" numeric(3,2),
    "ai_processing_time_ms" integer,
    "ai_model_used" character varying(100),
    "ai_tokens_consumed" integer,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "processed_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "context_data" jsonb,
    "response_data" jsonb,
    "error_details" jsonb,
    "owner_user_id" uuid,
    "owner_username" character varying(150),
    "owner_email" character varying(254),
    "workspace_id" uuid,
    "workspace_name" character varying(255),
    "tenant_id" uuid,
    "tenant_name" character varying(255),
    "tenant_slug" character varying(100),
    "deployment_environment" character varying(50),
    "deployment_region" character varying(100),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb
);

ALTER TABLE "infrastructure_aiagentquery" ADD CONSTRAINT "infrastructure_aiagentquery_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_created_2bafeb_idx ON public.infrastructure_aiagentquery USING btree (created_at);
CREATE INDEX infrastruct_owner_u_dff6dc_idx ON public.infrastructure_aiagentquery USING btree (owner_user_id);
CREATE INDEX infrastruct_priorit_963c4d_idx ON public.infrastructure_aiagentquery USING btree (priority);
CREATE INDEX infrastruct_process_9e9af0_idx ON public.infrastructure_aiagentquery USING btree (processed_at);
CREATE INDEX infrastruct_query_t_279b1b_idx ON public.infrastructure_aiagentquery USING btree (query_type);
CREATE INDEX infrastruct_session_d8b227_idx ON public.infrastructure_aiagentquery USING btree (session_id);
CREATE INDEX infrastruct_status_0adaac_idx ON public.infrastructure_aiagentquery USING btree (status);
CREATE INDEX infrastruct_tenant__0b29c5_idx ON public.infrastructure_aiagentquery USING btree (tenant_id);
CREATE INDEX infrastruct_tenant__8cc827_idx ON public.infrastructure_aiagentquery USING btree (tenant_slug);
CREATE INDEX infrastruct_workspa_cb6a97_idx ON public.infrastructure_aiagentquery USING btree (workspace_id);
CREATE INDEX infrastructure_aiagentquery_tenant_slug_4f2b5795 ON public.infrastructure_aiagentquery USING btree (tenant_slug);
CREATE INDEX infrastructure_aiagentquery_tenant_slug_4f2b5795_like ON public.infrastructure_aiagentquery USING btree (tenant_slug varchar_pattern_ops);

-- -----------------------------------------------
-- Table: infrastructure_aiagentrecommendation
-- -----------------------------------------------
CREATE TABLE "infrastructure_aiagentrecommendation" (
    "id" uuid NOT NULL,
    "query_id" uuid,
    "recommendation_type" character varying(50) NOT NULL,
    "title" character varying(255) NOT NULL,
    "description" text NOT NULL,
    "confidence_score" numeric(3,2),
    "priority_rank" integer,
    "estimated_cost" numeric(10,2),
    "estimated_savings" numeric(10,2),
    "implementation_time_minutes" integer,
    "risk_level" character varying(20) NOT NULL,
    "risk_details" jsonb,
    "prerequisites" jsonb NOT NULL,
    "implementation_steps" jsonb NOT NULL,
    "rollback_plan" jsonb,
    "tags" jsonb NOT NULL,
    "metadata" jsonb NOT NULL,
    "status" character varying(30) NOT NULL,
    "expires_at" timestamp with time zone,
    "ai_model_version" character varying(100),
    "ai_generation_context" jsonb,
    "ai_similar_recommendations" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "reviewed_at" timestamp with time zone,
    "implemented_at" timestamp with time zone,
    "implementation_results" jsonb,
    "user_feedback" jsonb,
    "owner_user_id" uuid,
    "owner_username" character varying(150),
    "owner_email" character varying(254),
    "workspace_id" uuid,
    "workspace_name" character varying(255),
    "tenant_id" uuid,
    "tenant_name" character varying(255),
    "tenant_slug" character varying(100),
    "deployment_environment" character varying(50),
    "deployment_region" character varying(100),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb
);

ALTER TABLE "infrastructure_aiagentrecommendation" ADD CONSTRAINT "infrastructure_aiagentrecommendation_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_confide_54b0e5_idx ON public.infrastructure_aiagentrecommendation USING btree (confidence_score);
CREATE INDEX infrastruct_created_d9fc0b_idx ON public.infrastructure_aiagentrecommendation USING btree (created_at);
CREATE INDEX infrastruct_expires_2f431d_idx ON public.infrastructure_aiagentrecommendation USING btree (expires_at);
CREATE INDEX infrastruct_owner_u_a51e70_idx ON public.infrastructure_aiagentrecommendation USING btree (owner_user_id);
CREATE INDEX infrastruct_priorit_060ede_idx ON public.infrastructure_aiagentrecommendation USING btree (priority_rank);
CREATE INDEX infrastruct_query_i_065805_idx ON public.infrastructure_aiagentrecommendation USING btree (query_id);
CREATE INDEX infrastruct_recomme_b2c711_idx ON public.infrastructure_aiagentrecommendation USING btree (recommendation_type);
CREATE INDEX infrastruct_risk_le_704fee_idx ON public.infrastructure_aiagentrecommendation USING btree (risk_level);
CREATE INDEX infrastruct_status_846ab5_idx ON public.infrastructure_aiagentrecommendation USING btree (status);
CREATE INDEX infrastruct_tenant__7d6a43_idx ON public.infrastructure_aiagentrecommendation USING btree (tenant_slug);
CREATE INDEX infrastruct_tenant__aa3a46_idx ON public.infrastructure_aiagentrecommendation USING btree (tenant_id);
CREATE INDEX infrastruct_workspa_2145ff_idx ON public.infrastructure_aiagentrecommendation USING btree (workspace_id);
CREATE INDEX infrastructure_aiagentrecommendation_tenant_slug_17087975 ON public.infrastructure_aiagentrecommendation USING btree (tenant_slug);
CREATE INDEX infrastructure_aiagentrecommendation_tenant_slug_17087975_like ON public.infrastructure_aiagentrecommendation USING btree (tenant_slug varchar_pattern_ops);

-- -----------------------------------------------
-- Table: infrastructure_billingsnapshot
-- -----------------------------------------------
CREATE TABLE "infrastructure_billingsnapshot" (
    "id" uuid NOT NULL,
    "provider" character varying(50) NOT NULL,
    "snapshot_date" date NOT NULL,
    "total_cost" numeric(15,2) NOT NULL,
    "currency" character varying(10) NOT NULL,
    "breakdown" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "billing_period_start" date,
    "billing_period_end" date,
    "billing_status" character varying(20) NOT NULL,
    "payment_method" character varying(50),
    "invoice_number" character varying(100),
    "cost_allocation_tags" jsonb,
    "optimization_recommendations" jsonb,
    "payment_due_date" date,
    "payment_date" date,
    "payment_reference" character varying(100),
    "ai_savings_estimate" numeric(15,2),
    "ai_cost_forecasting" jsonb,
    "ai_recommendation_accepted" boolean,
    "ai_output_impact" jsonb,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "state_facts" jsonb,
    "reports" jsonb,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "workspace_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_billingsnapshot" ADD CONSTRAINT "infrastructure_billi_workspace_id_908cefad_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "infrastructure_billingsnapshot" ADD CONSTRAINT "infrastructure_billingsnapshot_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_billing_b9f682_idx ON public.infrastructure_billingsnapshot USING btree (billing_status);
CREATE INDEX infrastruct_created_afd123_idx ON public.infrastructure_billingsnapshot USING btree (created_at);
CREATE INDEX infrastruct_invoice_57a4b0_idx ON public.infrastructure_billingsnapshot USING btree (invoice_number);
CREATE INDEX infrastruct_payment_5aac4c_idx ON public.infrastructure_billingsnapshot USING btree (payment_due_date);
CREATE INDEX infrastruct_updated_a65fa5_idx ON public.infrastructure_billingsnapshot USING btree (updated_at);
CREATE INDEX infrastruct_workspa_09e587_idx ON public.infrastructure_billingsnapshot USING btree (workspace_id, provider, snapshot_date);
CREATE INDEX infrastructure_billingsnapshot_workspace_id_908cefad ON public.infrastructure_billingsnapshot USING btree (workspace_id);

-- -----------------------------------------------
-- Table: infrastructure_chatconversation
-- -----------------------------------------------
CREATE TABLE "infrastructure_chatconversation" (
    "id" uuid NOT NULL,
    "title" character varying(255),
    "conversation_type" character varying(50) NOT NULL,
    "agent_type" character varying(50) NOT NULL,
    "status" character varying(20) NOT NULL,
    "context_data" jsonb NOT NULL,
    "conversation_summary" text,
    "current_topic" character varying(255),
    "agent_personality" jsonb NOT NULL,
    "agent_capabilities" jsonb NOT NULL,
    "agent_knowledge_base" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "last_activity" timestamp with time zone NOT NULL,
    "expires_at" timestamp with time zone,
    "message_count" integer NOT NULL,
    "user_satisfaction_score" numeric(3,2),
    "resolution_status" character varying(50),
    "escalation_reason" text,
    "related_workspace_id" uuid,
    "related_operations" jsonb NOT NULL,
    "related_queries" jsonb NOT NULL,
    "conversation_tags" jsonb NOT NULL,
    "bookmarked" boolean NOT NULL,
    "priority_level" character varying(20) NOT NULL,
    "owner_user_id" uuid,
    "owner_username" character varying(150),
    "owner_email" character varying(254),
    "workspace_id" uuid,
    "workspace_name" character varying(255),
    "tenant_id" uuid,
    "tenant_name" character varying(255),
    "tenant_slug" character varying(100),
    "deployment_environment" character varying(50),
    "deployment_region" character varying(100),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb
);

ALTER TABLE "infrastructure_chatconversation" ADD CONSTRAINT "infrastructure_chatconversation_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_agent_t_35bf74_idx ON public.infrastructure_chatconversation USING btree (agent_type);
CREATE INDEX infrastruct_convers_a6dc1e_idx ON public.infrastructure_chatconversation USING btree (conversation_type);
CREATE INDEX infrastruct_created_9968f5_idx ON public.infrastructure_chatconversation USING btree (created_at);
CREATE INDEX infrastruct_last_ac_aa07b8_idx ON public.infrastructure_chatconversation USING btree (last_activity);
CREATE INDEX infrastruct_owner_u_4144ef_idx ON public.infrastructure_chatconversation USING btree (owner_user_id);
CREATE INDEX infrastruct_priorit_7dda0f_idx ON public.infrastructure_chatconversation USING btree (priority_level);
CREATE INDEX infrastruct_related_0ae83b_idx ON public.infrastructure_chatconversation USING btree (related_workspace_id);
CREATE INDEX infrastruct_status_f9b9d2_idx ON public.infrastructure_chatconversation USING btree (status);
CREATE INDEX infrastruct_tenant__a6215c_idx ON public.infrastructure_chatconversation USING btree (tenant_id);
CREATE INDEX infrastruct_tenant__b9a44c_idx ON public.infrastructure_chatconversation USING btree (tenant_slug);
CREATE INDEX infrastruct_workspa_17e541_idx ON public.infrastructure_chatconversation USING btree (workspace_id);
CREATE INDEX infrastructure_chatconversation_tenant_slug_67c8dacc ON public.infrastructure_chatconversation USING btree (tenant_slug);
CREATE INDEX infrastructure_chatconversation_tenant_slug_67c8dacc_like ON public.infrastructure_chatconversation USING btree (tenant_slug varchar_pattern_ops);

-- -----------------------------------------------
-- Table: infrastructure_chatmessage
-- -----------------------------------------------
CREATE TABLE "infrastructure_chatmessage" (
    "id" uuid NOT NULL,
    "content" text NOT NULL,
    "content_type" character varying(30) NOT NULL,
    "message_type" character varying(30) NOT NULL,
    "status" character varying(20) NOT NULL,
    "is_edited" boolean NOT NULL,
    "edit_count" integer NOT NULL,
    "original_content" text,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "read_at" timestamp with time zone,
    "delivered_at" timestamp with time zone,
    "ai_processing_time_ms" integer,
    "ai_model_used" character varying(100),
    "ai_tokens_used" integer,
    "ai_confidence_score" numeric(3,2),
    "thread_id" uuid,
    "sequence_number" integer NOT NULL,
    "attachments" jsonb NOT NULL,
    "code_snippets" jsonb NOT NULL,
    "infrastructure_references" jsonb NOT NULL,
    "reactions" jsonb NOT NULL,
    "flagged" boolean NOT NULL,
    "flagged_reason" character varying(255),
    "triggered_actions" jsonb NOT NULL,
    "tool_calls" jsonb NOT NULL,
    "action_results" jsonb NOT NULL,
    "context_used" jsonb NOT NULL,
    "memory_updated" jsonb NOT NULL,
    "owner_user_id" uuid,
    "owner_username" character varying(150),
    "owner_email" character varying(254),
    "workspace_id" uuid,
    "workspace_name" character varying(255),
    "tenant_id" uuid,
    "tenant_name" character varying(255),
    "tenant_slug" character varying(100),
    "deployment_environment" character varying(50),
    "deployment_region" character varying(100),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "conversation_id" uuid NOT NULL,
    "parent_message_id" uuid
);

ALTER TABLE "infrastructure_chatmessage" ADD CONSTRAINT "infrastructure_chatm_conversation_id_20731ed1_fk_infrastru" FOREIGN KEY ("conversation_id") REFERENCES "infrastructure_chatconversation" ("id");
ALTER TABLE "infrastructure_chatmessage" ADD CONSTRAINT "infrastructure_chatm_parent_message_id_ceca5812_fk_infrastru" FOREIGN KEY ("parent_message_id") REFERENCES "infrastructure_chatmessage" ("id");
ALTER TABLE "infrastructure_chatmessage" ADD CONSTRAINT "infrastructure_chatmessage_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_convers_8d1b7e_idx ON public.infrastructure_chatmessage USING btree (conversation_id, sequence_number);
CREATE INDEX infrastruct_created_f8cfe8_idx ON public.infrastructure_chatmessage USING btree (created_at);
CREATE INDEX infrastruct_message_330e9b_idx ON public.infrastructure_chatmessage USING btree (message_type);
CREATE INDEX infrastruct_owner_u_b078df_idx ON public.infrastructure_chatmessage USING btree (owner_user_id);
CREATE INDEX infrastruct_parent__f71a98_idx ON public.infrastructure_chatmessage USING btree (parent_message_id);
CREATE INDEX infrastruct_status_1ef3eb_idx ON public.infrastructure_chatmessage USING btree (status);
CREATE INDEX infrastruct_tenant__4c0b37_idx ON public.infrastructure_chatmessage USING btree (tenant_slug);
CREATE INDEX infrastruct_tenant__fd3e27_idx ON public.infrastructure_chatmessage USING btree (tenant_id);
CREATE INDEX infrastruct_thread__e19708_idx ON public.infrastructure_chatmessage USING btree (thread_id);
CREATE INDEX infrastruct_workspa_b10496_idx ON public.infrastructure_chatmessage USING btree (workspace_id);
CREATE INDEX infrastructure_chatmessage_conversation_id_20731ed1 ON public.infrastructure_chatmessage USING btree (conversation_id);
CREATE INDEX infrastructure_chatmessage_parent_message_id_ceca5812 ON public.infrastructure_chatmessage USING btree (parent_message_id);
CREATE INDEX infrastructure_chatmessage_tenant_slug_299c2862 ON public.infrastructure_chatmessage USING btree (tenant_slug);
CREATE INDEX infrastructure_chatmessage_tenant_slug_299c2862_like ON public.infrastructure_chatmessage USING btree (tenant_slug varchar_pattern_ops);

-- -----------------------------------------------
-- Table: infrastructure_cloudmetrics
-- -----------------------------------------------
CREATE TABLE "infrastructure_cloudmetrics" (
    "id" uuid NOT NULL,
    "provider" character varying(50) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    "metric_type" character varying(50) NOT NULL,
    "metric_data" jsonb NOT NULL,
    "resource_id" character varying(255) NOT NULL,
    "resource_type" character varying(100) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "metric_unit" character varying(50),
    "aggregation_method" character varying(50),
    "threshold_values" jsonb,
    "metric_tags" jsonb,
    "alert_enabled" boolean NOT NULL,
    "alert_conditions" jsonb,
    "state_facts" jsonb,
    "reports" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "workspace_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_cloudmetrics" ADD CONSTRAINT "infrastructure_cloud_workspace_id_7af0c508_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "infrastructure_cloudmetrics" ADD CONSTRAINT "infrastructure_cloudmetrics_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_alert_e_af508c_idx ON public.infrastructure_cloudmetrics USING btree (alert_enabled);
CREATE INDEX infrastruct_created_fb8c60_idx ON public.infrastructure_cloudmetrics USING btree (created_at);
CREATE INDEX infrastruct_metric__3da67f_idx ON public.infrastructure_cloudmetrics USING btree (metric_type, resource_id);
CREATE INDEX infrastruct_metric__8efc91_idx ON public.infrastructure_cloudmetrics USING btree (metric_unit);
CREATE INDEX infrastruct_updated_d02be9_idx ON public.infrastructure_cloudmetrics USING btree (updated_at);
CREATE INDEX infrastruct_workspa_f6f98f_idx ON public.infrastructure_cloudmetrics USING btree (workspace_id, provider, "timestamp");
CREATE INDEX infrastructure_cloudmetrics_workspace_id_7af0c508 ON public.infrastructure_cloudmetrics USING btree (workspace_id);

-- -----------------------------------------------
-- Table: infrastructure_cloudoperation
-- -----------------------------------------------
CREATE TABLE "infrastructure_cloudoperation" (
    "id" uuid NOT NULL,
    "session_id" character varying(255),
    "operation_type" character varying(50) NOT NULL,
    "status" character varying(50) NOT NULL,
    "resource_type" character varying(100) NOT NULL,
    "resource_name" character varying(255) NOT NULL,
    "configuration" jsonb NOT NULL,
    "error_message" text,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "workflow_state" jsonb,
    "message" character varying(255),
    "current_step" integer,
    "environment" character varying(64) NOT NULL,
    "domain_name" character varying(255),
    "custom_domain_name" character varying(255),
    "alternate_domain_names" jsonb,
    "application_files_storage" character varying(255),
    "ssl_certificate_arn" character varying(255),
    "ssl_certificate_status" character varying(50),
    "dns_records" jsonb,
    "dns_provider" character varying(50),
    "dns_zone_id" character varying(255),
    "cloud_provider" character varying(20),
    "cloud_region" character varying(50),
    "cloud_account_id" character varying(100),
    "kubernetes_namespace" character varying(255),
    "kubernetes_cluster" character varying(255),
    "kubernetes_context" character varying(255),
    "kubeernetes_miscelaneous" jsonb,
    "kubernetes_reserved_field_1" text,
    "kubernetes_reserved_field_2" text,
    "kubernetes_reserved_field_3" text,
    "kubernetes_reserved_field_4" text,
    "kubernetes_reserved_field_5" text,
    "kubernetes_reserved_list_1" jsonb,
    "kubernetes_reserved_list_2" jsonb,
    "kubernetes_reserved_list_3" jsonb,
    "state_facts" jsonb,
    "reports" jsonb,
    "state_path" character varying(255),
    "state_backend" character varying,
    "state_backend_source" jsonb,
    "state_bucket" character varying(255),
    "state_key" character varying(255),
    "source_code" text,
    "source_code_hash" character varying(64),
    "source_code_format" character varying,
    "ai_risk_assessment" jsonb,
    "ai_completion_prediction" jsonb,
    "ai_code_adopted" boolean,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "web_hosting_params_1" character varying,
    "web_hosting_params_2" character varying,
    "web_hosting_params_3" character varying,
    "web_hosting_params_6" jsonb,
    "web_hosting_params_9" jsonb,
    "extended_editable_field_1" character varying,
    "extended_editable_field_2" character varying,
    "extended_editable_field_3" character varying,
    "extended_editable_field_4" character varying,
    "extended_editable_field_5" character varying,
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "workflow_id" uuid,
    "workspace_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_cloudoperation" ADD CONSTRAINT "infrastructure_cloud_workflow_id_6909f16e_fk_infrastru" FOREIGN KEY ("workflow_id") REFERENCES "infrastructure_workflowdefinition" ("id");
ALTER TABLE "infrastructure_cloudoperation" ADD CONSTRAINT "infrastructure_cloud_workspace_id_71378a4b_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "infrastructure_cloudoperation" ADD CONSTRAINT "infrastructure_cloudoperation_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_cloud_p_814c63_idx ON public.infrastructure_cloudoperation USING btree (cloud_provider);
CREATE INDEX infrastruct_domain__58a13a_idx ON public.infrastructure_cloudoperation USING btree (domain_name);
CREATE INDEX infrastruct_environ_5b4488_idx ON public.infrastructure_cloudoperation USING btree (environment);
CREATE INDEX infrastruct_operati_b6c8d4_idx ON public.infrastructure_cloudoperation USING btree (operation_type);
CREATE INDEX infrastruct_resourc_ee2ce7_idx ON public.infrastructure_cloudoperation USING btree (resource_type);
CREATE INDEX infrastruct_session_387336_idx ON public.infrastructure_cloudoperation USING btree (session_id);
CREATE INDEX infrastruct_source__4e6fdf_idx ON public.infrastructure_cloudoperation USING btree (source_code_hash);
CREATE INDEX infrastruct_status_c4220a_idx ON public.infrastructure_cloudoperation USING btree (status);
CREATE INDEX infrastruct_workspa_5fbfe6_idx ON public.infrastructure_cloudoperation USING btree (workspace_id);
CREATE INDEX infrastructure_cloudoperation_workflow_id_6909f16e ON public.infrastructure_cloudoperation USING btree (workflow_id);
CREATE INDEX infrastructure_cloudoperation_workspace_id_71378a4b ON public.infrastructure_cloudoperation USING btree (workspace_id);

-- -----------------------------------------------
-- Table: infrastructure_credentialconnection
-- -----------------------------------------------
CREATE TABLE "infrastructure_credentialconnection" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "service" character varying(50) NOT NULL,
    "connection_type" character varying(50) NOT NULL,
    "config" jsonb NOT NULL,
    "is_active" boolean NOT NULL,
    "is_verified" boolean NOT NULL,
    "last_used" timestamp with time zone,
    "usage_count" integer NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "infrastructure_credentialconnection" ADD CONSTRAINT "infrastructure_crede_user_id_552a0225_fk_users_use" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "infrastructure_credentialconnection" ADD CONSTRAINT "infrastructure_credentialconnection_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_credentialconnection" ADD CONSTRAINT "infrastructure_credentia_user_id_name_service_f9c7d7c7_uniq" UNIQUE ("user_id", "name", "service");
ALTER TABLE "infrastructure_credentialconnection" ADD CONSTRAINT "infrastructure_credentia_user_id_name_service_f9c7d7c7_uniq" UNIQUE ("user_id", "name", "service");
ALTER TABLE "infrastructure_credentialconnection" ADD CONSTRAINT "infrastructure_credentia_user_id_name_service_f9c7d7c7_uniq" UNIQUE ("user_id", "name", "service");

CREATE INDEX infrastruct_is_acti_f79871_idx ON public.infrastructure_credentialconnection USING btree (is_active);
CREATE INDEX infrastruct_last_us_8d4f48_idx ON public.infrastructure_credentialconnection USING btree (last_used DESC);
CREATE INDEX infrastruct_user_id_7c74cd_idx ON public.infrastructure_credentialconnection USING btree (user_id, service);
CREATE UNIQUE INDEX infrastructure_credentia_user_id_name_service_f9c7d7c7_uniq ON public.infrastructure_credentialconnection USING btree (user_id, name, service);
CREATE INDEX infrastructure_credentialconnection_service_3112ac9b ON public.infrastructure_credentialconnection USING btree (service);
CREATE INDEX infrastructure_credentialconnection_service_3112ac9b_like ON public.infrastructure_credentialconnection USING btree (service varchar_pattern_ops);
CREATE INDEX infrastructure_credentialconnection_user_id_552a0225 ON public.infrastructure_credentialconnection USING btree (user_id);

-- -----------------------------------------------
-- Table: infrastructure_domainregistrar
-- -----------------------------------------------
CREATE TABLE "infrastructure_domainregistrar" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "provider" character varying(50) NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "domain_name" character varying(255) NOT NULL,
    "registration_date" timestamp with time zone NOT NULL,
    "expiry_date" timestamp with time zone NOT NULL,
    "auto_renew" boolean NOT NULL,
    "domain_status" character varying(50) NOT NULL,
    "registrant_contact" jsonb NOT NULL,
    "admin_contact" jsonb NOT NULL,
    "technical_contact" jsonb NOT NULL,
    "billing_contact" jsonb NOT NULL,
    "nameservers" jsonb NOT NULL,
    "dns_records" jsonb NOT NULL,
    "dns_provider" character varying(100),
    "ssl_certificates" jsonb NOT NULL,
    "ssl_provider" character varying(100),
    "ssl_auto_renewal" boolean NOT NULL,
    "privacy_protection" boolean NOT NULL,
    "privacy_provider" character varying(100),
    "transfer_lock" boolean NOT NULL,
    "registrar_lock" boolean NOT NULL,
    "email_forwarding" jsonb NOT NULL,
    "domain_forwarding" jsonb NOT NULL,
    "dnssec_enabled" boolean NOT NULL,
    "state_facts" jsonb,
    "reports" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model" character varying,
    "ai_instruction" character varying,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "workspace_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_domainregistrar" ADD CONSTRAINT "infrastructure_domai_workspace_id_7e338990_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "infrastructure_domainregistrar" ADD CONSTRAINT "infrastructure_domainregistrar_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_domainregistrar" ADD CONSTRAINT "infrastructure_domainregistrar_domain_name_key" UNIQUE ("domain_name");

CREATE INDEX infrastruct_domain__6c1bd6_idx ON public.infrastructure_domainregistrar USING btree (domain_name);
CREATE INDEX infrastruct_provide_c69ce1_idx ON public.infrastructure_domainregistrar USING btree (provider);
CREATE INDEX infrastruct_workspa_de6f52_idx ON public.infrastructure_domainregistrar USING btree (workspace_id);
CREATE INDEX infrastructure_domainregistrar_domain_name_80799fed_like ON public.infrastructure_domainregistrar USING btree (domain_name varchar_pattern_ops);
CREATE UNIQUE INDEX infrastructure_domainregistrar_domain_name_key ON public.infrastructure_domainregistrar USING btree (domain_name);
CREATE INDEX infrastructure_domainregistrar_workspace_id_7e338990 ON public.infrastructure_domainregistrar USING btree (workspace_id);

-- -----------------------------------------------
-- Table: infrastructure_iactemplate
-- -----------------------------------------------
CREATE TABLE "infrastructure_iactemplate" (
    "id" uuid NOT NULL,
    "name" character varying(200) NOT NULL,
    "description" text NOT NULL,
    "format" character varying(20) NOT NULL,
    "source_code" text NOT NULL,
    "version" character varying(50) NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "storage_backend" character varying(20) NOT NULL,
    "storage_bucket" character varying(255),
    "storage_path" character varying(255),
    "storage_url" character varying(500),
    "default_branch" character varying(100),
    "state_facts" jsonb,
    "reports" jsonb,
    "cloud_provider" character varying(20),
    "tags" jsonb NOT NULL,
    "parameters" jsonb NOT NULL,
    "outputs" jsonb NOT NULL,
    "git_repository" character varying(500),
    "git_branch" character varying(100),
    "git_commit" character varying(100),
    "ai_compliance_score" jsonb,
    "ai_security_vulnerabilities" jsonb,
    "ai_template_adopted" boolean,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model" character varying,
    "ai_description" character varying,
    "ai_instruction" character varying,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "cloud_operation_id" uuid
);

ALTER TABLE "infrastructure_iactemplate" ADD CONSTRAINT "infrastructure_iacte_cloud_operation_id_94773b1e_fk_infrastru" FOREIGN KEY ("cloud_operation_id") REFERENCES "infrastructure_cloudoperation" ("id");
ALTER TABLE "infrastructure_iactemplate" ADD CONSTRAINT "infrastructure_iactemplate_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_cloud_o_ea0ef6_idx ON public.infrastructure_iactemplate USING btree (cloud_operation_id);
CREATE INDEX infrastruct_cloud_p_3631ed_idx ON public.infrastructure_iactemplate USING btree (cloud_provider);
CREATE INDEX infrastruct_format_1b8e54_idx ON public.infrastructure_iactemplate USING btree (format);
CREATE INDEX infrastruct_is_acti_b26b99_idx ON public.infrastructure_iactemplate USING btree (is_active);
CREATE INDEX infrastructure_iactemplate_cloud_operation_id_94773b1e ON public.infrastructure_iactemplate USING btree (cloud_operation_id);

-- -----------------------------------------------
-- Table: infrastructure_mcpserverregistry
-- -----------------------------------------------
CREATE TABLE "infrastructure_mcpserverregistry" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text,
    "server_type" character varying(50) NOT NULL,
    "connection_string" character varying(1000) NOT NULL,
    "protocol_version" character varying(20) NOT NULL,
    "endpoint_url" character varying(200),
    "capabilities" jsonb NOT NULL,
    "configuration" jsonb NOT NULL,
    "authentication" jsonb NOT NULL,
    "status" character varying(20) NOT NULL,
    "last_heartbeat" timestamp with time zone,
    "health_check_url" character varying(200),
    "health_check_interval" integer NOT NULL,
    "error_message" text,
    "retry_count" integer NOT NULL,
    "max_retries" integer NOT NULL,
    "retry_delay_seconds" integer NOT NULL,
    "is_system" boolean NOT NULL,
    "is_enabled" boolean NOT NULL,
    "version" character varying(50),
    "total_requests" bigint NOT NULL,
    "successful_requests" bigint NOT NULL,
    "failed_requests" bigint NOT NULL,
    "average_response_time_ms" double precision,
    "rate_limit_per_minute" integer NOT NULL,
    "rate_limit_per_hour" integer NOT NULL,
    "current_usage_count" integer NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "last_accessed" timestamp with time zone,
    "tags" jsonb NOT NULL,
    "metadata" jsonb NOT NULL,
    "security_level" character varying(20) NOT NULL,
    "compliance_requirements" jsonb NOT NULL,
    "access_permissions" jsonb NOT NULL,
    "owner_user_id" uuid,
    "owner_username" character varying(150),
    "owner_email" character varying(254),
    "workspace_id" uuid,
    "workspace_name" character varying(255),
    "tenant_id" uuid,
    "tenant_name" character varying(255),
    "tenant_slug" character varying(100),
    "deployment_environment" character varying(50),
    "deployment_region" character varying(100),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb
);

ALTER TABLE "infrastructure_mcpserverregistry" ADD CONSTRAINT "infrastructure_mcpserverregistry_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_mcpserverregistry" ADD CONSTRAINT "infrastructure_mcpserverregistry_name_key" UNIQUE ("name");

CREATE INDEX infrastruct_created_7c9a42_idx ON public.infrastructure_mcpserverregistry USING btree (created_at);
CREATE INDEX infrastruct_deploym_6bdacd_idx ON public.infrastructure_mcpserverregistry USING btree (deployment_environment);
CREATE INDEX infrastruct_is_enab_9036b6_idx ON public.infrastructure_mcpserverregistry USING btree (is_enabled);
CREATE INDEX infrastruct_is_syst_fff052_idx ON public.infrastructure_mcpserverregistry USING btree (is_system);
CREATE INDEX infrastruct_last_ac_f8ab1c_idx ON public.infrastructure_mcpserverregistry USING btree (last_accessed);
CREATE INDEX infrastruct_last_he_293d23_idx ON public.infrastructure_mcpserverregistry USING btree (last_heartbeat);
CREATE INDEX infrastruct_name_c5e913_idx ON public.infrastructure_mcpserverregistry USING btree (name);
CREATE INDEX infrastruct_owner_u_aee636_idx ON public.infrastructure_mcpserverregistry USING btree (owner_user_id);
CREATE INDEX infrastruct_server__26af31_idx ON public.infrastructure_mcpserverregistry USING btree (server_type);
CREATE INDEX infrastruct_status_9a014f_idx ON public.infrastructure_mcpserverregistry USING btree (status);
CREATE INDEX infrastruct_tenant__6e7117_idx ON public.infrastructure_mcpserverregistry USING btree (tenant_id);
CREATE INDEX infrastruct_tenant__df5c49_idx ON public.infrastructure_mcpserverregistry USING btree (tenant_slug);
CREATE INDEX infrastruct_workspa_eceb1d_idx ON public.infrastructure_mcpserverregistry USING btree (workspace_id);
CREATE INDEX infrastructure_mcpserverregistry_name_ee2b6e59_like ON public.infrastructure_mcpserverregistry USING btree (name varchar_pattern_ops);
CREATE UNIQUE INDEX infrastructure_mcpserverregistry_name_key ON public.infrastructure_mcpserverregistry USING btree (name);
CREATE INDEX infrastructure_mcpserverregistry_tenant_slug_44d8a775 ON public.infrastructure_mcpserverregistry USING btree (tenant_slug);
CREATE INDEX infrastructure_mcpserverregistry_tenant_slug_44d8a775_like ON public.infrastructure_mcpserverregistry USING btree (tenant_slug varchar_pattern_ops);

-- -----------------------------------------------
-- Table: infrastructure_namespace
-- -----------------------------------------------
CREATE TABLE "infrastructure_namespace" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "environment" character varying(50) NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "description" text NOT NULL,
    "labels" jsonb NOT NULL,
    "annotations" jsonb NOT NULL,
    "cpu_limit" character varying(20),
    "memory_limit" character varying(20),
    "storage_limit" character varying(20),
    "pod_limit" integer,
    "network_policies" jsonb NOT NULL,
    "ingress_rules" jsonb NOT NULL,
    "egress_rules" jsonb NOT NULL,
    "service_accounts" jsonb NOT NULL,
    "rbac_rules" jsonb NOT NULL,
    "pod_security_policies" jsonb NOT NULL,
    "monitoring_enabled" boolean NOT NULL,
    "alert_configuration" jsonb NOT NULL,
    "logging_enabled" boolean NOT NULL,
    "log_retention_days" integer NOT NULL,
    "state_facts" jsonb,
    "reports" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model" character varying,
    "ai_instruction" character varying,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "workspace_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_namespace" ADD CONSTRAINT "infrastructure_names_workspace_id_9512ba17_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "infrastructure_namespace" ADD CONSTRAINT "infrastructure_namespace_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_namespace" ADD CONSTRAINT "infrastructure_namespace_workspace_id_name_enviro_5ee5cea8_uniq" UNIQUE ("workspace_id", "name", "environment");
ALTER TABLE "infrastructure_namespace" ADD CONSTRAINT "infrastructure_namespace_workspace_id_name_enviro_5ee5cea8_uniq" UNIQUE ("workspace_id", "name", "environment");
ALTER TABLE "infrastructure_namespace" ADD CONSTRAINT "infrastructure_namespace_workspace_id_name_enviro_5ee5cea8_uniq" UNIQUE ("workspace_id", "name", "environment");

CREATE INDEX infrastruct_environ_663c29_idx ON public.infrastructure_namespace USING btree (environment);
CREATE INDEX infrastruct_workspa_7e9ef7_idx ON public.infrastructure_namespace USING btree (workspace_id);
CREATE INDEX infrastructure_namespace_workspace_id_9512ba17 ON public.infrastructure_namespace USING btree (workspace_id);
CREATE UNIQUE INDEX infrastructure_namespace_workspace_id_name_enviro_5ee5cea8_uniq ON public.infrastructure_namespace USING btree (workspace_id, name, environment);

-- -----------------------------------------------
-- Table: infrastructure_nodeexecutionresult
-- -----------------------------------------------
CREATE TABLE "infrastructure_nodeexecutionresult" (
    "id" uuid NOT NULL,
    "node_id" character varying(255) NOT NULL,
    "node_type" character varying(100),
    "success" boolean NOT NULL,
    "start_time" timestamp with time zone NOT NULL,
    "end_time" timestamp with time zone,
    "duration" double precision NOT NULL,
    "output" jsonb,
    "error" text,
    "logs" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "workflow_execution_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_nodeexecutionresult" ADD CONSTRAINT "infrastructure_nodee_workflow_execution_i_470b8f5d_fk_infrastru" FOREIGN KEY ("workflow_execution_id") REFERENCES "infrastructure_workflowexecution" ("id");
ALTER TABLE "infrastructure_nodeexecutionresult" ADD CONSTRAINT "infrastructure_nodeexecutionresult_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_node_ty_6070e7_idx ON public.infrastructure_nodeexecutionresult USING btree (node_type);
CREATE INDEX infrastruct_success_fec5f5_idx ON public.infrastructure_nodeexecutionresult USING btree (success);
CREATE INDEX infrastruct_workflo_4d96e0_idx ON public.infrastructure_nodeexecutionresult USING btree (workflow_execution_id, node_id);
CREATE INDEX infrastructure_nodeexecuti_workflow_execution_id_470b8f5d ON public.infrastructure_nodeexecutionresult USING btree (workflow_execution_id);
CREATE INDEX infrastructure_nodeexecutionresult_node_id_4f4aac65 ON public.infrastructure_nodeexecutionresult USING btree (node_id);
CREATE INDEX infrastructure_nodeexecutionresult_node_id_4f4aac65_like ON public.infrastructure_nodeexecutionresult USING btree (node_id varchar_pattern_ops);

-- -----------------------------------------------
-- Table: infrastructure_sitesettings
-- -----------------------------------------------
CREATE TABLE "infrastructure_sitesettings" (
    "id" uuid NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "site_identity" jsonb NOT NULL,
    "seo" jsonb NOT NULL,
    "domain" jsonb NOT NULL,
    "media" jsonb NOT NULL,
    "performance" jsonb NOT NULL,
    "communication" jsonb NOT NULL,
    "social_media" jsonb NOT NULL,
    "localization" jsonb NOT NULL,
    "legal" jsonb NOT NULL,
    "business" jsonb NOT NULL,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "workspace_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_sitesettings" ADD CONSTRAINT "infrastructure_sites_workspace_id_e16fb706_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "infrastructure_sitesettings" ADD CONSTRAINT "infrastructure_sitesettings_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_sitesettings" ADD CONSTRAINT "infrastructure_sitesettings_workspace_id_e16fb706_uniq" UNIQUE ("workspace_id");

CREATE INDEX infrastruct_workspa_ebe093_idx ON public.infrastructure_sitesettings USING btree (workspace_id);
CREATE INDEX infrastructure_sitesettings_workspace_id_e16fb706 ON public.infrastructure_sitesettings USING btree (workspace_id);
CREATE UNIQUE INDEX infrastructure_sitesettings_workspace_id_e16fb706_uniq ON public.infrastructure_sitesettings USING btree (workspace_id);

-- -----------------------------------------------
-- Table: infrastructure_webhosting
-- -----------------------------------------------
CREATE TABLE "infrastructure_webhosting" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "hosting_provider" character varying(50) NOT NULL,
    "hosting_plan" character varying(100) NOT NULL,
    "hosting_region" character varying(100) NOT NULL,
    "server_type" character varying(50) NOT NULL,
    "server_configuration" jsonb NOT NULL,
    "server_os" character varying(100) NOT NULL,
    "domain_name" character varying(255) NOT NULL,
    "website_type" character varying(50) NOT NULL,
    "php_version" character varying(20),
    "database_type" character varying(50),
    "ssl_enabled" boolean NOT NULL,
    "ssl_provider" character varying(100),
    "ssl_expiry" timestamp with time zone,
    "bandwidth_limit" bigint,
    "storage_limit" bigint,
    "email_accounts_limit" integer,
    "database_limit" integer,
    "backup_enabled" boolean NOT NULL,
    "backup_frequency" character varying(50),
    "backup_retention" integer,
    "last_backup" timestamp with time zone,
    "firewall_enabled" boolean NOT NULL,
    "firewall_rules" jsonb NOT NULL,
    "ddos_protection" boolean NOT NULL,
    "waf_enabled" boolean NOT NULL,
    "monitoring_enabled" boolean NOT NULL,
    "alert_email" character varying(254),
    "uptime_monitoring" boolean NOT NULL,
    "resource_monitoring" boolean NOT NULL,
    "custom_configuration" jsonb NOT NULL,
    "environment_variables" jsonb NOT NULL,
    "deployment_hooks" jsonb NOT NULL,
    "state_facts" jsonb,
    "reports" jsonb,
    "session_id" character varying(255),
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model" character varying,
    "ai_instruction" character varying,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "workspace_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_webhosting" ADD CONSTRAINT "infrastructure_webho_workspace_id_dec39367_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "infrastructure_webhosting" ADD CONSTRAINT "infrastructure_webhosting_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_domain__413aa9_idx ON public.infrastructure_webhosting USING btree (domain_name);
CREATE INDEX infrastruct_hosting_b2b81e_idx ON public.infrastructure_webhosting USING btree (hosting_provider);
CREATE INDEX infrastruct_workspa_b2ab72_idx ON public.infrastructure_webhosting USING btree (workspace_id);
CREATE INDEX infrastructure_webhosting_workspace_id_dec39367 ON public.infrastructure_webhosting USING btree (workspace_id);

-- -----------------------------------------------
-- Table: infrastructure_workflowdefinition
-- -----------------------------------------------
CREATE TABLE "infrastructure_workflowdefinition" (
    "id" uuid NOT NULL,
    "session_id" character varying(255),
    "name" character varying(255),
    "version" character varying(50) NOT NULL,
    "description" text NOT NULL,
    "nodes" jsonb,
    "edges" jsonb,
    "configuration" jsonb,
    "trigger" jsonb,
    "error_handling" character varying(50) NOT NULL,
    "timezone" character varying(50) NOT NULL,
    "retry_attempts" integer NOT NULL,
    "settings" jsonb,
    "layout" jsonb,
    "is_active" boolean NOT NULL,
    "status" character varying(50) NOT NULL,
    "state_facts" jsonb,
    "reports" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "git_repository" character varying(500),
    "git_branch" character varying(100),
    "git_commit" character varying(100),
    "ai_workflow_suggestions" jsonb,
    "ai_design_feedback" jsonb,
    "ai_workflow_adopted" boolean,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model" character varying,
    "ai_description" character varying,
    "ai_instruction" character varying,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "user_id" bigint
);

ALTER TABLE "infrastructure_workflowdefinition" ADD CONSTRAINT "infrastructure_workf_user_id_3ea03048_fk_users_use" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "infrastructure_workflowdefinition" ADD CONSTRAINT "infrastructure_workflowdefinition_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_is_acti_266dce_idx ON public.infrastructure_workflowdefinition USING btree (is_active);
CREATE INDEX infrastruct_name_ecf07a_idx ON public.infrastructure_workflowdefinition USING btree (name);
CREATE INDEX infrastruct_session_653dde_idx ON public.infrastructure_workflowdefinition USING btree (session_id);
CREATE INDEX infrastruct_user_id_d0bb9d_idx ON public.infrastructure_workflowdefinition USING btree (user_id);
CREATE INDEX infrastruct_version_e6018b_idx ON public.infrastructure_workflowdefinition USING btree (version);
CREATE INDEX infrastructure_workflowdefinition_user_id_3ea03048 ON public.infrastructure_workflowdefinition USING btree (user_id);

-- -----------------------------------------------
-- Table: infrastructure_workflowexecution
-- -----------------------------------------------
CREATE TABLE "infrastructure_workflowexecution" (
    "id" uuid NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "status" character varying(50) NOT NULL,
    "start_time" timestamp with time zone NOT NULL,
    "end_time" timestamp with time zone,
    "duration" double precision NOT NULL,
    "result" jsonb,
    "error" text,
    "logs" jsonb,
    "terraform_config" text,
    "yaml_config" text,
    "json_config" text,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "created_by_id" bigint,
    "workflow_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_workflowexecution" ADD CONSTRAINT "infrastructure_workf_created_by_id_a3d80045_fk_users_use" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "infrastructure_workflowexecution" ADD CONSTRAINT "infrastructure_workf_workflow_id_94a17e55_fk_infrastru" FOREIGN KEY ("workflow_id") REFERENCES "infrastructure_workflowdefinition" ("id");
ALTER TABLE "infrastructure_workflowexecution" ADD CONSTRAINT "infrastructure_workflowexecution_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_workflowexecution" ADD CONSTRAINT "infrastructure_workflowexecution_session_id_key" UNIQUE ("session_id");

CREATE INDEX infrastruct_created_18047d_idx ON public.infrastructure_workflowexecution USING btree (created_by_id);
CREATE INDEX infrastruct_session_205791_idx ON public.infrastructure_workflowexecution USING btree (session_id);
CREATE INDEX infrastruct_start_t_fa2eb8_idx ON public.infrastructure_workflowexecution USING btree (start_time DESC);
CREATE INDEX infrastruct_status_9e86b0_idx ON public.infrastructure_workflowexecution USING btree (status);
CREATE INDEX infrastruct_workflo_a855bf_idx ON public.infrastructure_workflowexecution USING btree (workflow_id, status);
CREATE INDEX infrastructure_workflowexecution_created_by_id_a3d80045 ON public.infrastructure_workflowexecution USING btree (created_by_id);
CREATE INDEX infrastructure_workflowexecution_session_id_890721bf_like ON public.infrastructure_workflowexecution USING btree (session_id varchar_pattern_ops);
CREATE UNIQUE INDEX infrastructure_workflowexecution_session_id_key ON public.infrastructure_workflowexecution USING btree (session_id);
CREATE INDEX infrastructure_workflowexecution_status_43e8eb29 ON public.infrastructure_workflowexecution USING btree (status);
CREATE INDEX infrastructure_workflowexecution_status_43e8eb29_like ON public.infrastructure_workflowexecution USING btree (status varchar_pattern_ops);
CREATE INDEX infrastructure_workflowexecution_workflow_id_94a17e55 ON public.infrastructure_workflowexecution USING btree (workflow_id);

-- -----------------------------------------------
-- Table: infrastructure_workflowtemplate
-- -----------------------------------------------
CREATE TABLE "infrastructure_workflowtemplate" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text NOT NULL,
    "category" character varying(50) NOT NULL,
    "tags" jsonb,
    "template_data" jsonb NOT NULL,
    "is_public" boolean NOT NULL,
    "is_featured" boolean NOT NULL,
    "usage_count" integer NOT NULL,
    "version" character varying(50) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "created_by_id" bigint
);

ALTER TABLE "infrastructure_workflowtemplate" ADD CONSTRAINT "infrastructure_workf_created_by_id_c0006850_fk_users_use" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "infrastructure_workflowtemplate" ADD CONSTRAINT "infrastructure_workflowtemplate_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_categor_c2aaeb_idx ON public.infrastructure_workflowtemplate USING btree (category);
CREATE INDEX infrastruct_created_632aab_idx ON public.infrastructure_workflowtemplate USING btree (created_by_id);
CREATE INDEX infrastruct_is_publ_118575_idx ON public.infrastructure_workflowtemplate USING btree (is_public, is_featured);
CREATE INDEX infrastruct_usage_c_e2674d_idx ON public.infrastructure_workflowtemplate USING btree (usage_count DESC);
CREATE INDEX infrastructure_workflowtemplate_category_61ec0f0c ON public.infrastructure_workflowtemplate USING btree (category);
CREATE INDEX infrastructure_workflowtemplate_category_61ec0f0c_like ON public.infrastructure_workflowtemplate USING btree (category varchar_pattern_ops);
CREATE INDEX infrastructure_workflowtemplate_created_by_id_c0006850 ON public.infrastructure_workflowtemplate USING btree (created_by_id);

-- -----------------------------------------------
-- Table: infrastructure_workflowvalidation
-- -----------------------------------------------
CREATE TABLE "infrastructure_workflowvalidation" (
    "id" uuid NOT NULL,
    "valid" boolean NOT NULL,
    "errors" jsonb,
    "warnings" jsonb,
    "validated_at" timestamp with time zone NOT NULL,
    "validated_by_id" bigint,
    "workflow_id" uuid NOT NULL
);

ALTER TABLE "infrastructure_workflowvalidation" ADD CONSTRAINT "infrastructure_workf_validated_by_id_fd61894f_fk_users_use" FOREIGN KEY ("validated_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "infrastructure_workflowvalidation" ADD CONSTRAINT "infrastructure_workf_workflow_id_3eb2fecb_fk_infrastru" FOREIGN KEY ("workflow_id") REFERENCES "infrastructure_workflowdefinition" ("id");
ALTER TABLE "infrastructure_workflowvalidation" ADD CONSTRAINT "infrastructure_workflowvalidation_pkey" PRIMARY KEY ("id");

CREATE INDEX infrastruct_valid_648aac_idx ON public.infrastructure_workflowvalidation USING btree (valid);
CREATE INDEX infrastruct_workflo_4f5d92_idx ON public.infrastructure_workflowvalidation USING btree (workflow_id, validated_at DESC);
CREATE INDEX infrastructure_workflowvalidation_validated_by_id_fd61894f ON public.infrastructure_workflowvalidation USING btree (validated_by_id);
CREATE INDEX infrastructure_workflowvalidation_workflow_id_3eb2fecb ON public.infrastructure_workflowvalidation USING btree (workflow_id);

-- -----------------------------------------------
-- Table: infrastructure_workspace
-- -----------------------------------------------
CREATE TABLE "infrastructure_workspace" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "is_active" boolean NOT NULL,
    "is_default_workspace" boolean NOT NULL,
    "session_id" uuid NOT NULL,
    "configuration" jsonb NOT NULL,
    "hashicorp_workspace_id" character varying(64),
    "hashicorp_organization" character varying(64),
    "hashicorp_token" character varying(64),
    "hashicorp_address" character varying(64),
    "hashicorp_token_expiration" timestamp with time zone,
    "Vault_workspace_id" character varying(64),
    "Vault_organization" character varying(64),
    "Vault_token" character varying(64),
    "Vault_address" character varying(64),
    "Vault_token_expiration" timestamp with time zone,
    "state_facts" jsonb,
    "reports" jsonb,
    "state_management_storage" character varying(64),
    "state_management_provider" character varying(64),
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(64),
    "extended_editable_field_2" character varying(64),
    "extended_editable_field_3" character varying(64),
    "extended_editable_field_4" character varying(64),
    "extended_editable_field_5" character varying(64),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "insta_node_id" bigint,
    "organization_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "infrastructure_workspace" ADD CONSTRAINT "infrastructure_works_insta_node_id_f197634e_fk_users_ins" FOREIGN KEY ("insta_node_id") REFERENCES "users_instanodebox" ("id");
ALTER TABLE "infrastructure_workspace" ADD CONSTRAINT "infrastructure_works_organization_id_6271eeeb_fk_users_org" FOREIGN KEY ("organization_id") REFERENCES "users_organization" ("id");
ALTER TABLE "infrastructure_workspace" ADD CONSTRAINT "infrastructure_workspace_user_id_3e85a613_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "infrastructure_workspace" ADD CONSTRAINT "infrastructure_workspace_pkey" PRIMARY KEY ("id");
ALTER TABLE "infrastructure_workspace" ADD CONSTRAINT "infrastructure_workspace_user_id_name_9eddd08b_uniq" UNIQUE ("user_id", "name");
ALTER TABLE "infrastructure_workspace" ADD CONSTRAINT "infrastructure_workspace_user_id_name_9eddd08b_uniq" UNIQUE ("user_id", "name");

CREATE INDEX infrastruct_organiz_c2c095_idx ON public.infrastructure_workspace USING btree (organization_id);
CREATE INDEX infrastruct_session_841ba8_idx ON public.infrastructure_workspace USING btree (session_id);
CREATE INDEX infrastruct_user_id_b7dc9b_idx ON public.infrastructure_workspace USING btree (user_id);
CREATE INDEX infrastructure_workspace_insta_node_id_f197634e ON public.infrastructure_workspace USING btree (insta_node_id);
CREATE INDEX infrastructure_workspace_organization_id_6271eeeb ON public.infrastructure_workspace USING btree (organization_id);
CREATE INDEX infrastructure_workspace_user_id_3e85a613 ON public.infrastructure_workspace USING btree (user_id);
CREATE UNIQUE INDEX infrastructure_workspace_user_id_name_9eddd08b_uniq ON public.infrastructure_workspace USING btree (user_id, name);

-- -----------------------------------------------
-- Table: leads
-- -----------------------------------------------
CREATE TABLE "leads" (
    "id" integer NOT NULL,
    "contact_person" character varying(255),
    "business_name" character varying(255) NOT NULL,
    "email" character varying(254),
    "category" character varying(255),
    "address" text,
    "city" character varying(100),
    "state" character varying(100),
    "postal" character varying(20),
    "country" character varying(100),
    "phone_number" character varying(50),
    "website" text,
    "facebook_page" text,
    "twitter" text,
    "linkedin" text,
    "enrichment_source" character varying(255),
    "sent" boolean NOT NULL,
    "clicked" boolean NOT NULL,
    "replied" boolean NOT NULL,
    "contact_found" character varying(10),
    "called" character varying(10) NOT NULL,
    "follow_up" character varying(10) NOT NULL,
    "notes" text NOT NULL,
    "recommendation" text NOT NULL,
    "sales_representative" character varying(255) NOT NULL,
    "date_generated" timestamp with time zone NOT NULL,
    "industry" character varying(255),
    "lead_respond" character varying(10) NOT NULL,
    "sent_sms" character varying(10) NOT NULL,
    "lead_quality" character varying(20) NOT NULL,
    "meeting_booked" character varying(20) NOT NULL,
    "meeting_date" timestamp with time zone,
    "deal_closed" character varying(20) NOT NULL,
    "deal_value" numeric(10,2),
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb,
    "sales_rep_id" integer
);

ALTER TABLE "leads" ADD CONSTRAINT "leads_sales_rep_id_e6dee79b_fk_sales_representatives_id" FOREIGN KEY ("sales_rep_id") REFERENCES "sales_representatives" ("id");
ALTER TABLE "leads" ADD CONSTRAINT "leads_pkey" PRIMARY KEY ("id");
ALTER TABLE "leads" ADD CONSTRAINT "leads_business_name_key" UNIQUE ("business_name");

CREATE INDEX idx_business_name ON public.leads USING btree (business_name);
CREATE INDEX idx_contact_found ON public.leads USING btree (contact_found);
CREATE INDEX idx_date_generated ON public.leads USING btree (date_generated);
CREATE INDEX idx_deal_value ON public.leads USING btree (deal_value) WHERE (deal_value IS NOT NULL);
CREATE INDEX idx_email_not_found ON public.leads USING btree (email) WHERE ((email IS NULL) OR ((email)::text = ''::text) OR ((email)::text = 'not found'::text));
CREATE INDEX idx_follow_up ON public.leads USING btree (follow_up) WHERE ((follow_up)::text = 'YES'::text);
CREATE INDEX idx_lead_quality ON public.leads USING btree (lead_quality);
CREATE INDEX idx_meeting_date ON public.leads USING btree (meeting_date) WHERE (meeting_date IS NOT NULL);
CREATE INDEX idx_sales_rep_id ON public.leads USING btree (sales_rep_id);
CREATE INDEX idx_sales_representative ON public.leads USING btree (sales_representative);
CREATE INDEX leads_business_name_e2b499c0_like ON public.leads USING btree (business_name varchar_pattern_ops);
CREATE UNIQUE INDEX leads_business_name_key ON public.leads USING btree (business_name);
CREATE INDEX leads_sales_rep_id_e6dee79b ON public.leads USING btree (sales_rep_id);
CREATE UNIQUE INDEX unique_email_when_valid ON public.leads USING btree (email) WHERE ((email IS NOT NULL) AND (NOT (((email)::text = ''::text) AND (email IS NOT NULL))) AND (NOT (((email)::text = 'not found'::text) AND (email IS NOT NULL))));

-- -----------------------------------------------
-- Table: marketplace_aiproductdescription
-- -----------------------------------------------
CREATE TABLE "marketplace_aiproductdescription" (
    "id" uuid NOT NULL,
    "version" integer NOT NULL,
    "title" character varying(300) NOT NULL,
    "short_description" text NOT NULL,
    "long_description" text NOT NULL,
    "key_features" jsonb NOT NULL,
    "sustainability_highlights" text NOT NULL,
    "meta_title" character varying(60) NOT NULL,
    "meta_description" character varying(160) NOT NULL,
    "focus_keywords" jsonb NOT NULL,
    "ai_model_used" character varying(50) NOT NULL,
    "prompt_template" text NOT NULL,
    "generation_status" character varying(20) NOT NULL,
    "quality_score" double precision,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "ai_risk_assessment" jsonb,
    "ai_completion_prediction" jsonb,
    "ai_code_adopted" boolean,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "product_id" uuid NOT NULL
);

ALTER TABLE "marketplace_aiproductdescription" ADD CONSTRAINT "marketplace_aiproduc_product_id_fadc2878_fk_marketpla" FOREIGN KEY ("product_id") REFERENCES "marketplace_product" ("id");
ALTER TABLE "marketplace_aiproductdescription" ADD CONSTRAINT "marketplace_aiproductdescription_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_aiproductdescription" ADD CONSTRAINT "marketplace_aiproductdes_product_id_version_614feeda_uniq" UNIQUE ("product_id", "version");
ALTER TABLE "marketplace_aiproductdescription" ADD CONSTRAINT "marketplace_aiproductdes_product_id_version_614feeda_uniq" UNIQUE ("product_id", "version");

CREATE UNIQUE INDEX marketplace_aiproductdes_product_id_version_614feeda_uniq ON public.marketplace_aiproductdescription USING btree (product_id, version);
CREATE INDEX marketplace_aiproductdescription_product_id_fadc2878 ON public.marketplace_aiproductdescription USING btree (product_id);

-- -----------------------------------------------
-- Table: marketplace_brand
-- -----------------------------------------------
CREATE TABLE "marketplace_brand" (
    "id" uuid NOT NULL,
    "name" character varying(200) NOT NULL,
    "description" text NOT NULL,
    "website" character varying(200) NOT NULL,
    "logo" character varying(100),
    "sustainability_focus" text NOT NULL,
    "target_audience" character varying(500) NOT NULL,
    "brand_voice" character varying(100) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_risk_assessment" jsonb,
    "ai_completion_prediction" jsonb,
    "ai_code_adopted" boolean,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "user_id" bigint NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_brand" ADD CONSTRAINT "marketplace_brand_user_id_f114e1d5_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "marketplace_brand" ADD CONSTRAINT "marketplace_brand_pkey" PRIMARY KEY ("id");

CREATE INDEX marketplace_brand_user_id_f114e1d5 ON public.marketplace_brand USING btree (user_id);

-- -----------------------------------------------
-- Table: marketplace_brandsettings
-- -----------------------------------------------
CREATE TABLE "marketplace_brandsettings" (
    "id" bigint NOT NULL,
    "primary_color" character varying(7) NOT NULL,
    "secondary_color" character varying(7) NOT NULL,
    "background_color" character varying(7) NOT NULL,
    "text_color" character varying(7) NOT NULL,
    "font_family" character varying(100) NOT NULL,
    "app_name" character varying(100) NOT NULL,
    "logo_url" character varying(200),
    "favicon_url" character varying(200),
    "supported_currencies" jsonb NOT NULL,
    "payment_methods" jsonb NOT NULL,
    "transaction_fees" double precision NOT NULL,
    "minimum_amount" double precision NOT NULL,
    "shopify_api_key" character varying(255),
    "shopify_api_secret" character varying(255),
    "gmail_api_key" character varying(255),
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "brand_id" uuid NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_brandsettings" ADD CONSTRAINT "marketplace_brandset_brand_id_99d44d1c_fk_marketpla" FOREIGN KEY ("brand_id") REFERENCES "marketplace_brand" ("id");
ALTER TABLE "marketplace_brandsettings" ADD CONSTRAINT "marketplace_brandsettings_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_brandsettings" ADD CONSTRAINT "marketplace_brandsettings_brand_id_key" UNIQUE ("brand_id");

CREATE UNIQUE INDEX marketplace_brandsettings_brand_id_key ON public.marketplace_brandsettings USING btree (brand_id);

-- -----------------------------------------------
-- Table: marketplace_contentgeneration
-- -----------------------------------------------
CREATE TABLE "marketplace_contentgeneration" (
    "id" uuid NOT NULL,
    "content_type" character varying(30) NOT NULL,
    "prompt_used" text NOT NULL,
    "input_data" jsonb NOT NULL,
    "generated_content" text NOT NULL,
    "tokens_used" integer NOT NULL,
    "generation_time" double precision NOT NULL,
    "model_used" character varying(50) NOT NULL,
    "readability_score" double precision,
    "seo_score" double precision,
    "authenticity_score" double precision,
    "created_at" timestamp with time zone NOT NULL,
    "user_id" bigint NOT NULL,
    "product_id" uuid,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_contentgeneration" ADD CONSTRAINT "marketplace_contentg_product_id_920f39ae_fk_marketpla" FOREIGN KEY ("product_id") REFERENCES "marketplace_product" ("id");
ALTER TABLE "marketplace_contentgeneration" ADD CONSTRAINT "marketplace_contentgeneration_user_id_763d8bdb_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "marketplace_contentgeneration" ADD CONSTRAINT "marketplace_contentgeneration_pkey" PRIMARY KEY ("id");

CREATE INDEX marketplace_contentgeneration_product_id_920f39ae ON public.marketplace_contentgeneration USING btree (product_id);
CREATE INDEX marketplace_contentgeneration_user_id_763d8bdb ON public.marketplace_contentgeneration USING btree (user_id);

-- -----------------------------------------------
-- Table: marketplace_crawledpage
-- -----------------------------------------------
CREATE TABLE "marketplace_crawledpage" (
    "id" bigint NOT NULL,
    "url" character varying(200) NOT NULL,
    "status_code" integer NOT NULL,
    "load_time" double precision NOT NULL,
    "page_size" integer NOT NULL,
    "title" character varying(500) NOT NULL,
    "meta_description" text NOT NULL,
    "h1_text" character varying(500) NOT NULL,
    "h2_count" integer NOT NULL,
    "image_count" integer NOT NULL,
    "internal_links" integer NOT NULL,
    "external_links" integer NOT NULL,
    "indexable" boolean NOT NULL,
    "has_title" boolean NOT NULL,
    "has_meta_description" boolean NOT NULL,
    "has_h1" boolean NOT NULL,
    "title_length" integer NOT NULL,
    "meta_description_length" integer NOT NULL,
    "word_count" integer NOT NULL,
    "readability_score" double precision,
    "content_type" character varying(100) NOT NULL,
    "canonical_url" character varying(200) NOT NULL,
    "robots_meta" character varying(200) NOT NULL,
    "page_depth" integer NOT NULL,
    "issues" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "crawl_id" uuid NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_crawledpage" ADD CONSTRAINT "marketplace_crawledp_crawl_id_482a6c02_fk_marketpla" FOREIGN KEY ("crawl_id") REFERENCES "marketplace_siteauditcrawl" ("id");
ALTER TABLE "marketplace_crawledpage" ADD CONSTRAINT "marketplace_crawledpage_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_crawledpage" ADD CONSTRAINT "marketplace_crawledpage_crawl_id_url_88163ff6_uniq" UNIQUE ("crawl_id", "url");
ALTER TABLE "marketplace_crawledpage" ADD CONSTRAINT "marketplace_crawledpage_crawl_id_url_88163ff6_uniq" UNIQUE ("crawl_id", "url");

CREATE INDEX marketplace_crawledpage_crawl_id_482a6c02 ON public.marketplace_crawledpage USING btree (crawl_id);
CREATE UNIQUE INDEX marketplace_crawledpage_crawl_id_url_88163ff6_uniq ON public.marketplace_crawledpage USING btree (crawl_id, url);

-- -----------------------------------------------
-- Table: marketplace_googleanalyticsintegration
-- -----------------------------------------------
CREATE TABLE "marketplace_googleanalyticsintegration" (
    "id" bigint NOT NULL,
    "property_id" character varying(50) NOT NULL,
    "view_id" character varying(50) NOT NULL,
    "access_token" text NOT NULL,
    "refresh_token" text NOT NULL,
    "is_active" boolean NOT NULL,
    "last_sync" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "brand_id" uuid NOT NULL
);

ALTER TABLE "marketplace_googleanalyticsintegration" ADD CONSTRAINT "marketplace_googlean_brand_id_f497f7cc_fk_marketpla" FOREIGN KEY ("brand_id") REFERENCES "marketplace_brand" ("id");
ALTER TABLE "marketplace_googleanalyticsintegration" ADD CONSTRAINT "marketplace_googleanalyticsintegration_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_googleanalyticsintegration" ADD CONSTRAINT "marketplace_googleanalyticsintegration_brand_id_key" UNIQUE ("brand_id");

CREATE UNIQUE INDEX marketplace_googleanalyticsintegration_brand_id_key ON public.marketplace_googleanalyticsintegration USING btree (brand_id);

-- -----------------------------------------------
-- Table: marketplace_keyword
-- -----------------------------------------------
CREATE TABLE "marketplace_keyword" (
    "id" bigint NOT NULL,
    "keyword" character varying(200) NOT NULL,
    "keyword_type" character varying(20) NOT NULL,
    "search_volume" integer NOT NULL,
    "competition_score" double precision NOT NULL,
    "trend_score" double precision NOT NULL,
    "category" character varying(50) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_keyword" ADD CONSTRAINT "marketplace_keyword_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_keyword" ADD CONSTRAINT "marketplace_keyword_keyword_key" UNIQUE ("keyword");

CREATE INDEX marketplace_keyword_keyword_2416ecf1_like ON public.marketplace_keyword USING btree (keyword varchar_pattern_ops);
CREATE UNIQUE INDEX marketplace_keyword_keyword_key ON public.marketplace_keyword USING btree (keyword);

-- -----------------------------------------------
-- Table: marketplace_paidcustomer
-- -----------------------------------------------
CREATE TABLE "marketplace_paidcustomer" (
    "id" uuid NOT NULL,
    "payment_gateway" character varying(50) NOT NULL,
    "transaction_id" character varying(255),
    "amount_paid" numeric(10,2) NOT NULL,
    "currency" character varying(10) NOT NULL,
    "payment_date" timestamp with time zone NOT NULL,
    "metadata" jsonb,
    "brand_id" uuid NOT NULL,
    "user_id" bigint NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_paidcustomer" ADD CONSTRAINT "marketplace_paidcust_brand_id_ac25cc3d_fk_marketpla" FOREIGN KEY ("brand_id") REFERENCES "marketplace_brand" ("id");
ALTER TABLE "marketplace_paidcustomer" ADD CONSTRAINT "marketplace_paidcustomer_user_id_2aa5fe44_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "marketplace_paidcustomer" ADD CONSTRAINT "marketplace_paidcustomer_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_paidcustomer" ADD CONSTRAINT "marketplace_paidcustomer_transaction_id_key" UNIQUE ("transaction_id");
ALTER TABLE "marketplace_paidcustomer" ADD CONSTRAINT "marketplace_paidcustomer_user_id_brand_id_transac_5abde264_uniq" UNIQUE ("user_id", "brand_id", "transaction_id");
ALTER TABLE "marketplace_paidcustomer" ADD CONSTRAINT "marketplace_paidcustomer_user_id_brand_id_transac_5abde264_uniq" UNIQUE ("user_id", "brand_id", "transaction_id");
ALTER TABLE "marketplace_paidcustomer" ADD CONSTRAINT "marketplace_paidcustomer_user_id_brand_id_transac_5abde264_uniq" UNIQUE ("user_id", "brand_id", "transaction_id");

CREATE INDEX marketplace_paidcustomer_brand_id_ac25cc3d ON public.marketplace_paidcustomer USING btree (brand_id);
CREATE INDEX marketplace_paidcustomer_transaction_id_de64c973_like ON public.marketplace_paidcustomer USING btree (transaction_id varchar_pattern_ops);
CREATE UNIQUE INDEX marketplace_paidcustomer_transaction_id_key ON public.marketplace_paidcustomer USING btree (transaction_id);
CREATE INDEX marketplace_paidcustomer_user_id_2aa5fe44 ON public.marketplace_paidcustomer USING btree (user_id);
CREATE UNIQUE INDEX marketplace_paidcustomer_user_id_brand_id_transac_5abde264_uniq ON public.marketplace_paidcustomer USING btree (user_id, brand_id, transaction_id);

-- -----------------------------------------------
-- Table: marketplace_paymentlink
-- -----------------------------------------------
CREATE TABLE "marketplace_paymentlink" (
    "id" uuid NOT NULL,
    "amount" numeric(10,2),
    "currency" character varying(3) NOT NULL,
    "link_code" character varying(50) NOT NULL,
    "description" text NOT NULL,
    "is_active" boolean NOT NULL,
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "product_id" uuid,
    "user_id" bigint NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_paymentlink" ADD CONSTRAINT "marketplace_paymentl_product_id_47d83be8_fk_marketpla" FOREIGN KEY ("product_id") REFERENCES "marketplace_product" ("id");
ALTER TABLE "marketplace_paymentlink" ADD CONSTRAINT "marketplace_paymentlink_user_id_2d90e08b_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "marketplace_paymentlink" ADD CONSTRAINT "marketplace_paymentlink_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_paymentlink" ADD CONSTRAINT "marketplace_paymentlink_link_code_key" UNIQUE ("link_code");

CREATE INDEX marketplace_paymentlink_link_code_29f1bd63_like ON public.marketplace_paymentlink USING btree (link_code varchar_pattern_ops);
CREATE UNIQUE INDEX marketplace_paymentlink_link_code_key ON public.marketplace_paymentlink USING btree (link_code);
CREATE INDEX marketplace_paymentlink_product_id_47d83be8 ON public.marketplace_paymentlink USING btree (product_id);
CREATE INDEX marketplace_paymentlink_user_id_2d90e08b ON public.marketplace_paymentlink USING btree (user_id);

-- -----------------------------------------------
-- Table: marketplace_product
-- -----------------------------------------------
CREATE TABLE "marketplace_product" (
    "id" uuid NOT NULL,
    "name" character varying(300) NOT NULL,
    "category" character varying(50) NOT NULL,
    "price" numeric(10,2) NOT NULL,
    "currency" character varying(3) NOT NULL,
    "sku" character varying(100) NOT NULL,
    "materials" text NOT NULL,
    "colors" character varying(200) NOT NULL,
    "sizes" character varying(200) NOT NULL,
    "care_instructions" text NOT NULL,
    "sustainability_features" jsonb NOT NULL,
    "origin_country" character varying(100) NOT NULL,
    "certifications" text NOT NULL,
    "primary_image" character varying(100),
    "current_description" text NOT NULL,
    "meta_title" character varying(60) NOT NULL,
    "meta_description" character varying(160) NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_risk_assessment" jsonb,
    "ai_completion_prediction" jsonb,
    "ai_code_adopted" boolean,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "brand_id" uuid NOT NULL,
    "subscription_product_id" uuid
);

ALTER TABLE "marketplace_product" ADD CONSTRAINT "marketplace_product_brand_id_9ae3a6e6_fk_marketplace_brand_id" FOREIGN KEY ("brand_id") REFERENCES "marketplace_brand" ("id");
ALTER TABLE "marketplace_product" ADD CONSTRAINT "marketplace_product_subscription_product_b419c08b_fk_subscript" FOREIGN KEY ("subscription_product_id") REFERENCES "subscriptions_product" ("id");
ALTER TABLE "marketplace_product" ADD CONSTRAINT "marketplace_product_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_product" ADD CONSTRAINT "marketplace_product_sku_key" UNIQUE ("sku");

CREATE INDEX marketplace_product_brand_id_9ae3a6e6 ON public.marketplace_product USING btree (brand_id);
CREATE INDEX marketplace_product_sku_8f5dea24_like ON public.marketplace_product USING btree (sku varchar_pattern_ops);
CREATE UNIQUE INDEX marketplace_product_sku_key ON public.marketplace_product USING btree (sku);
CREATE INDEX marketplace_product_subscription_product_id_b419c08b ON public.marketplace_product USING btree (subscription_product_id);

-- -----------------------------------------------
-- Table: marketplace_productimage
-- -----------------------------------------------
CREATE TABLE "marketplace_productimage" (
    "id" bigint NOT NULL,
    "image" character varying(100) NOT NULL,
    "alt_text" character varying(200) NOT NULL,
    "is_primary" boolean NOT NULL,
    "order" integer NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "ai_risk_assessment" jsonb,
    "ai_completion_prediction" jsonb,
    "ai_code_adopted" boolean,
    "user_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "product_id" uuid NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "marketplace_productimage" ADD CONSTRAINT "marketplace_producti_product_id_2e3794d2_fk_marketpla" FOREIGN KEY ("product_id") REFERENCES "marketplace_product" ("id");
ALTER TABLE "marketplace_productimage" ADD CONSTRAINT "marketplace_productimage_pkey" PRIMARY KEY ("id");

CREATE INDEX marketplace_productimage_product_id_2e3794d2 ON public.marketplace_productimage USING btree (product_id);

-- -----------------------------------------------
-- Table: marketplace_productkeyword
-- -----------------------------------------------
CREATE TABLE "marketplace_productkeyword" (
    "id" bigint NOT NULL,
    "relevance_score" double precision NOT NULL,
    "current_ranking" integer,
    "target_ranking" integer NOT NULL,
    "keyword_id" bigint NOT NULL,
    "product_id" uuid NOT NULL
);

ALTER TABLE "marketplace_productkeyword" ADD CONSTRAINT "marketplace_productk_keyword_id_44fb574c_fk_marketpla" FOREIGN KEY ("keyword_id") REFERENCES "marketplace_keyword" ("id");
ALTER TABLE "marketplace_productkeyword" ADD CONSTRAINT "marketplace_productk_product_id_4b1520ca_fk_marketpla" FOREIGN KEY ("product_id") REFERENCES "marketplace_product" ("id");
ALTER TABLE "marketplace_productkeyword" ADD CONSTRAINT "marketplace_productkeyword_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_productkeyword" ADD CONSTRAINT "marketplace_productkeyword_product_id_keyword_id_baeca650_uniq" UNIQUE ("product_id", "keyword_id");
ALTER TABLE "marketplace_productkeyword" ADD CONSTRAINT "marketplace_productkeyword_product_id_keyword_id_baeca650_uniq" UNIQUE ("product_id", "keyword_id");

CREATE INDEX marketplace_productkeyword_keyword_id_44fb574c ON public.marketplace_productkeyword USING btree (keyword_id);
CREATE INDEX marketplace_productkeyword_product_id_4b1520ca ON public.marketplace_productkeyword USING btree (product_id);
CREATE UNIQUE INDEX marketplace_productkeyword_product_id_keyword_id_baeca650_uniq ON public.marketplace_productkeyword USING btree (product_id, keyword_id);

-- -----------------------------------------------
-- Table: marketplace_seoaudit
-- -----------------------------------------------
CREATE TABLE "marketplace_seoaudit" (
    "id" uuid NOT NULL,
    "audit_type" character varying(20) NOT NULL,
    "overall_score" integer NOT NULL,
    "content_score" integer NOT NULL,
    "technical_score" integer NOT NULL,
    "keyword_score" integer NOT NULL,
    "recommendations" jsonb NOT NULL,
    "issues_found" jsonb NOT NULL,
    "opportunities" jsonb NOT NULL,
    "organic_traffic" integer NOT NULL,
    "click_through_rate" double precision NOT NULL,
    "bounce_rate" double precision NOT NULL,
    "conversion_rate" double precision NOT NULL,
    "audit_date" timestamp with time zone NOT NULL,
    "brand_id" uuid NOT NULL,
    "product_id" uuid
);

ALTER TABLE "marketplace_seoaudit" ADD CONSTRAINT "marketplace_seoaudit_brand_id_1787b864_fk_marketplace_brand_id" FOREIGN KEY ("brand_id") REFERENCES "marketplace_brand" ("id");
ALTER TABLE "marketplace_seoaudit" ADD CONSTRAINT "marketplace_seoaudit_product_id_fc8199b3_fk_marketpla" FOREIGN KEY ("product_id") REFERENCES "marketplace_product" ("id");
ALTER TABLE "marketplace_seoaudit" ADD CONSTRAINT "marketplace_seoaudit_pkey" PRIMARY KEY ("id");

CREATE INDEX marketplace_seoaudit_brand_id_1787b864 ON public.marketplace_seoaudit USING btree (brand_id);
CREATE INDEX marketplace_seoaudit_product_id_fc8199b3 ON public.marketplace_seoaudit USING btree (product_id);

-- -----------------------------------------------
-- Table: marketplace_siteauditcrawl
-- -----------------------------------------------
CREATE TABLE "marketplace_siteauditcrawl" (
    "id" uuid NOT NULL,
    "base_url" character varying(200) NOT NULL,
    "max_pages" integer NOT NULL,
    "status" character varying(20) NOT NULL,
    "pages_crawled" integer NOT NULL,
    "pages_found" integer NOT NULL,
    "crawl_duration" double precision NOT NULL,
    "ssl_status" boolean NOT NULL,
    "crawlability" boolean NOT NULL,
    "site_health_score" integer NOT NULL,
    "average_load_time" double precision NOT NULL,
    "max_load_time" double precision NOT NULL,
    "slow_pages_count" integer NOT NULL,
    "critical_issues" integer NOT NULL,
    "warning_issues" integer NOT NULL,
    "error_log" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "brand_id" uuid NOT NULL,
    "seo_audit_id" uuid
);

ALTER TABLE "marketplace_siteauditcrawl" ADD CONSTRAINT "marketplace_siteaudi_brand_id_09faa6d9_fk_marketpla" FOREIGN KEY ("brand_id") REFERENCES "marketplace_brand" ("id");
ALTER TABLE "marketplace_siteauditcrawl" ADD CONSTRAINT "marketplace_siteaudi_seo_audit_id_afaca551_fk_marketpla" FOREIGN KEY ("seo_audit_id") REFERENCES "marketplace_seoaudit" ("id");
ALTER TABLE "marketplace_siteauditcrawl" ADD CONSTRAINT "marketplace_siteauditcrawl_pkey" PRIMARY KEY ("id");
ALTER TABLE "marketplace_siteauditcrawl" ADD CONSTRAINT "marketplace_siteauditcrawl_seo_audit_id_key" UNIQUE ("seo_audit_id");

CREATE INDEX marketplace_siteauditcrawl_brand_id_09faa6d9 ON public.marketplace_siteauditcrawl USING btree (brand_id);
CREATE UNIQUE INDEX marketplace_siteauditcrawl_seo_audit_id_key ON public.marketplace_siteauditcrawl USING btree (seo_audit_id);

-- -----------------------------------------------
-- Table: marketplace_useractivity
-- -----------------------------------------------
CREATE TABLE "marketplace_useractivity" (
    "id" bigint NOT NULL,
    "activity_type" character varying(30) NOT NULL,
    "description" character varying(200) NOT NULL,
    "metadata" jsonb NOT NULL,
    "ip_address" inet,
    "user_agent" text NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "marketplace_useractivity" ADD CONSTRAINT "marketplace_useractivity_user_id_bf3e88d3_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "marketplace_useractivity" ADD CONSTRAINT "marketplace_useractivity_pkey" PRIMARY KEY ("id");

CREATE INDEX marketplace_useractivity_user_id_bf3e88d3 ON public.marketplace_useractivity USING btree (user_id);

-- -----------------------------------------------
-- Table: message_attachments
-- -----------------------------------------------
CREATE TABLE "message_attachments" (
    "id" uuid NOT NULL,
    "file_name" character varying(255) NOT NULL,
    "original_file_name" character varying(255) NOT NULL,
    "file_size" bigint NOT NULL,
    "file_type" character varying(50) NOT NULL,
    "attachment_type" character varying(20) NOT NULL,
    "file_url" character varying(200) NOT NULL,
    "thumbnail_url" character varying(200),
    "file_path" character varying(500),
    "content_type" character varying(100),
    "is_chart_image" boolean NOT NULL,
    "chart_metadata" jsonb,
    "is_safe" boolean NOT NULL,
    "virus_scan_status" character varying(20) NOT NULL,
    "uploaded_at" timestamp with time zone NOT NULL,
    "message_id" uuid NOT NULL
);

ALTER TABLE "message_attachments" ADD CONSTRAINT "message_attachments_message_id_c7a3e22d_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "message_attachments" ADD CONSTRAINT "message_attachments_pkey" PRIMARY KEY ("id");

CREATE INDEX message_attachments_message_id_c7a3e22d ON public.message_attachments USING btree (message_id);

-- -----------------------------------------------
-- Table: message_reactions
-- -----------------------------------------------
CREATE TABLE "message_reactions" (
    "id" uuid NOT NULL,
    "emoji" character varying(10) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "message_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "message_reactions" ADD CONSTRAINT "message_reactions_message_id_7f9c0331_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "message_reactions" ADD CONSTRAINT "message_reactions_user_id_58a64546_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "message_reactions" ADD CONSTRAINT "message_reactions_pkey" PRIMARY KEY ("id");
ALTER TABLE "message_reactions" ADD CONSTRAINT "message_reactions_message_id_user_id_emoji_fdd133f6_uniq" UNIQUE ("message_id", "user_id", "emoji");
ALTER TABLE "message_reactions" ADD CONSTRAINT "message_reactions_message_id_user_id_emoji_fdd133f6_uniq" UNIQUE ("message_id", "user_id", "emoji");
ALTER TABLE "message_reactions" ADD CONSTRAINT "message_reactions_message_id_user_id_emoji_fdd133f6_uniq" UNIQUE ("message_id", "user_id", "emoji");

CREATE INDEX message_rea_message_7f9ef3_idx ON public.message_reactions USING btree (message_id, emoji);
CREATE INDEX message_reactions_message_id_7f9c0331 ON public.message_reactions USING btree (message_id);
CREATE UNIQUE INDEX message_reactions_message_id_user_id_emoji_fdd133f6_uniq ON public.message_reactions USING btree (message_id, user_id, emoji);
CREATE INDEX message_reactions_user_id_58a64546 ON public.message_reactions USING btree (user_id);

-- -----------------------------------------------
-- Table: message_read_receipts
-- -----------------------------------------------
CREATE TABLE "message_read_receipts" (
    "id" uuid NOT NULL,
    "delivered_at" timestamp with time zone,
    "read_at" timestamp with time zone,
    "is_delivered" boolean NOT NULL,
    "is_read" boolean NOT NULL,
    "delivery_method" character varying(20) NOT NULL,
    "read_receipt_requested" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "message_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "message_read_receipts" ADD CONSTRAINT "message_read_receipts_message_id_164ce2d6_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "message_read_receipts" ADD CONSTRAINT "message_read_receipts_user_id_7b468aba_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "message_read_receipts" ADD CONSTRAINT "message_read_receipts_pkey" PRIMARY KEY ("id");
ALTER TABLE "message_read_receipts" ADD CONSTRAINT "message_read_receipts_message_id_user_id_394681e0_uniq" UNIQUE ("message_id", "user_id");
ALTER TABLE "message_read_receipts" ADD CONSTRAINT "message_read_receipts_message_id_user_id_394681e0_uniq" UNIQUE ("message_id", "user_id");

CREATE INDEX message_rea_deliver_c5dee2_idx ON public.message_read_receipts USING btree (delivered_at);
CREATE INDEX message_rea_message_2d64f3_idx ON public.message_read_receipts USING btree (message_id, is_delivered);
CREATE INDEX message_rea_user_id_96fe7f_idx ON public.message_read_receipts USING btree (user_id, is_read);
CREATE INDEX message_read_receipts_message_id_164ce2d6 ON public.message_read_receipts USING btree (message_id);
CREATE UNIQUE INDEX message_read_receipts_message_id_user_id_394681e0_uniq ON public.message_read_receipts USING btree (message_id, user_id);
CREATE INDEX message_read_receipts_user_id_7b468aba ON public.message_read_receipts USING btree (user_id);

-- -----------------------------------------------
-- Table: messages
-- -----------------------------------------------
CREATE TABLE "messages" (
    "id" uuid NOT NULL,
    "content" text NOT NULL,
    "message_type" character varying(20) NOT NULL,
    "price_data" jsonb,
    "is_edited" boolean NOT NULL,
    "is_deleted" boolean NOT NULL,
    "is_pinned" boolean NOT NULL,
    "is_system_message" boolean NOT NULL,
    "is_flagged" boolean NOT NULL,
    "moderation_status" character varying(20) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "edited_at" timestamp with time zone,
    "deleted_at" timestamp with time zone,
    "view_count" integer NOT NULL,
    "reaction_count" integer NOT NULL,
    "metadata" jsonb,
    "reply_to_id" uuid,
    "room_id" uuid NOT NULL,
    "sender_id" bigint NOT NULL,
    "thread_root_id" uuid
);

ALTER TABLE "messages" ADD CONSTRAINT "messages_reply_to_id_59eac9e3_fk_messages_id" FOREIGN KEY ("reply_to_id") REFERENCES "messages" ("id");
ALTER TABLE "messages" ADD CONSTRAINT "messages_room_id_b1776ddb_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messages" ADD CONSTRAINT "messages_sender_id_dc5a0bbd_fk_users_user_id" FOREIGN KEY ("sender_id") REFERENCES "users_user" ("id");
ALTER TABLE "messages" ADD CONSTRAINT "messages_thread_root_id_b1e42aee_fk_messages_id" FOREIGN KEY ("thread_root_id") REFERENCES "messages" ("id");
ALTER TABLE "messages" ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");

CREATE INDEX messages_deleted_555c2c_idx ON public.messages USING btree (deleted_at);
CREATE INDEX messages_is_dele_eb1655_idx ON public.messages USING btree (is_deleted, moderation_status);
CREATE INDEX messages_reply_t_313c91_idx ON public.messages USING btree (reply_to_id);
CREATE INDEX messages_reply_to_id_59eac9e3 ON public.messages USING btree (reply_to_id);
CREATE INDEX messages_room_id_72ec70_idx ON public.messages USING btree (room_id, created_at);
CREATE INDEX messages_room_id_b1776ddb ON public.messages USING btree (room_id);
CREATE INDEX messages_sender__bf8b1c_idx ON public.messages USING btree (sender_id, created_at);
CREATE INDEX messages_sender_id_dc5a0bbd ON public.messages USING btree (sender_id);
CREATE INDEX messages_thread_root_id_b1e42aee ON public.messages USING btree (thread_root_id);

-- -----------------------------------------------
-- Table: messaging_messageanalytics
-- -----------------------------------------------
CREATE TABLE "messaging_messageanalytics" (
    "id" uuid NOT NULL,
    "date" date NOT NULL,
    "total_messages" integer NOT NULL,
    "text_messages" integer NOT NULL,
    "image_messages" integer NOT NULL,
    "file_messages" integer NOT NULL,
    "active_users" integer NOT NULL,
    "new_participants" integer NOT NULL,
    "total_participants" integer NOT NULL,
    "total_reactions" integer NOT NULL,
    "total_replies" integer NOT NULL,
    "average_response_time" double precision,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "room_id" uuid NOT NULL
);

ALTER TABLE "messaging_messageanalytics" ADD CONSTRAINT "messaging_messageanalytics_room_id_e20af211_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_messageanalytics" ADD CONSTRAINT "messaging_messageanalytics_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_messageanalytics" ADD CONSTRAINT "messaging_messageanalytics_room_id_date_adf3b0f0_uniq" UNIQUE ("room_id", "date");
ALTER TABLE "messaging_messageanalytics" ADD CONSTRAINT "messaging_messageanalytics_room_id_date_adf3b0f0_uniq" UNIQUE ("room_id", "date");

CREATE UNIQUE INDEX messaging_messageanalytics_room_id_date_adf3b0f0_uniq ON public.messaging_messageanalytics USING btree (room_id, date);
CREATE INDEX messaging_messageanalytics_room_id_e20af211 ON public.messaging_messageanalytics USING btree (room_id);

-- -----------------------------------------------
-- Table: messaging_messagearchive
-- -----------------------------------------------
CREATE TABLE "messaging_messagearchive" (
    "id" uuid NOT NULL,
    "original_message_id" uuid NOT NULL,
    "content" text NOT NULL,
    "message_type" character varying(20) NOT NULL,
    "price_data" jsonb,
    "original_created_at" timestamp with time zone NOT NULL,
    "original_updated_at" timestamp with time zone NOT NULL,
    "archived_at" timestamp with time zone NOT NULL,
    "archived_reason" character varying(50) NOT NULL,
    "room_id" uuid NOT NULL,
    "sender_id" bigint NOT NULL
);

ALTER TABLE "messaging_messagearchive" ADD CONSTRAINT "messaging_messagearchive_room_id_5665041c_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_messagearchive" ADD CONSTRAINT "messaging_messagearchive_sender_id_ceef82a2_fk_users_user_id" FOREIGN KEY ("sender_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_messagearchive" ADD CONSTRAINT "messaging_messagearchive_pkey" PRIMARY KEY ("id");

CREATE INDEX messaging_m_origina_ac6c5e_idx ON public.messaging_messagearchive USING btree (original_message_id);
CREATE INDEX messaging_m_room_id_adeace_idx ON public.messaging_messagearchive USING btree (room_id, original_created_at);
CREATE INDEX messaging_messagearchive_original_message_id_40d77a8e ON public.messaging_messagearchive USING btree (original_message_id);
CREATE INDEX messaging_messagearchive_room_id_5665041c ON public.messaging_messagearchive USING btree (room_id);
CREATE INDEX messaging_messagearchive_sender_id_ceef82a2 ON public.messaging_messagearchive USING btree (sender_id);

-- -----------------------------------------------
-- Table: messaging_messageencryption
-- -----------------------------------------------
CREATE TABLE "messaging_messageencryption" (
    "id" uuid NOT NULL,
    "encryption_algorithm" character varying(50) NOT NULL,
    "key_id" character varying(255) NOT NULL,
    "iv" character varying(255),
    "encrypted_at" timestamp with time zone NOT NULL,
    "is_end_to_end" boolean NOT NULL,
    "message_id" uuid NOT NULL
);

ALTER TABLE "messaging_messageencryption" ADD CONSTRAINT "messaging_messageencryption_message_id_c81e2e4e_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "messaging_messageencryption" ADD CONSTRAINT "messaging_messageencryption_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_messageencryption" ADD CONSTRAINT "messaging_messageencryption_message_id_key" UNIQUE ("message_id");

CREATE UNIQUE INDEX messaging_messageencryption_message_id_key ON public.messaging_messageencryption USING btree (message_id);

-- -----------------------------------------------
-- Table: messaging_messagemention
-- -----------------------------------------------
CREATE TABLE "messaging_messagemention" (
    "id" uuid NOT NULL,
    "is_read" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "mentioned_user_id" bigint NOT NULL,
    "message_id" uuid NOT NULL
);

ALTER TABLE "messaging_messagemention" ADD CONSTRAINT "messaging_messagemen_mentioned_user_id_75178d42_fk_users_use" FOREIGN KEY ("mentioned_user_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_messagemention" ADD CONSTRAINT "messaging_messagemention_message_id_09e52799_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "messaging_messagemention" ADD CONSTRAINT "messaging_messagemention_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_messagemention" ADD CONSTRAINT "messaging_messagemention_message_id_mentioned_use_35dcd840_uniq" UNIQUE ("message_id", "mentioned_user_id");
ALTER TABLE "messaging_messagemention" ADD CONSTRAINT "messaging_messagemention_message_id_mentioned_use_35dcd840_uniq" UNIQUE ("message_id", "mentioned_user_id");

CREATE INDEX messaging_messagemention_mentioned_user_id_75178d42 ON public.messaging_messagemention USING btree (mentioned_user_id);
CREATE INDEX messaging_messagemention_message_id_09e52799 ON public.messaging_messagemention USING btree (message_id);
CREATE UNIQUE INDEX messaging_messagemention_message_id_mentioned_use_35dcd840_uniq ON public.messaging_messagemention USING btree (message_id, mentioned_user_id);

-- -----------------------------------------------
-- Table: messaging_messagepriority
-- -----------------------------------------------
CREATE TABLE "messaging_messagepriority" (
    "id" uuid NOT NULL,
    "priority_level" character varying(20) NOT NULL,
    "auto_escalate" boolean NOT NULL,
    "escalate_after_minutes" integer,
    "escalated_at" timestamp with time zone,
    "requires_acknowledgment" boolean NOT NULL,
    "send_push_notification" boolean NOT NULL,
    "send_email_notification" boolean NOT NULL,
    "send_sms_notification" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "message_id" uuid NOT NULL
);

ALTER TABLE "messaging_messagepriority" ADD CONSTRAINT "messaging_messagepriority_message_id_8a5bf846_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "messaging_messagepriority" ADD CONSTRAINT "messaging_messagepriority_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_messagepriority" ADD CONSTRAINT "messaging_messagepriority_message_id_key" UNIQUE ("message_id");

CREATE UNIQUE INDEX messaging_messagepriority_message_id_key ON public.messaging_messagepriority USING btree (message_id);

-- -----------------------------------------------
-- Table: messaging_messagetemplate
-- -----------------------------------------------
CREATE TABLE "messaging_messagetemplate" (
    "id" uuid NOT NULL,
    "name" character varying(100) NOT NULL,
    "description" text,
    "content" text NOT NULL,
    "template_type" character varying(20) NOT NULL,
    "variables" jsonb NOT NULL,
    "usage_count" integer NOT NULL,
    "is_public" boolean NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "created_by_id" bigint NOT NULL,
    "organization_id" uuid NOT NULL
);

ALTER TABLE "messaging_messagetemplate" ADD CONSTRAINT "messaging_messagetem_created_by_id_455b2daa_fk_users_use" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_messagetemplate" ADD CONSTRAINT "messaging_messagetem_organization_id_873371d7_fk_users_org" FOREIGN KEY ("organization_id") REFERENCES "users_organization" ("id");
ALTER TABLE "messaging_messagetemplate" ADD CONSTRAINT "messaging_messagetemplate_pkey" PRIMARY KEY ("id");

CREATE INDEX messaging_messagetemplate_created_by_id_455b2daa ON public.messaging_messagetemplate USING btree (created_by_id);
CREATE INDEX messaging_messagetemplate_organization_id_873371d7 ON public.messaging_messagetemplate USING btree (organization_id);

-- -----------------------------------------------
-- Table: messaging_moderationlog
-- -----------------------------------------------
CREATE TABLE "messaging_moderationlog" (
    "id" uuid NOT NULL,
    "action_type" character varying(20) NOT NULL,
    "reason" text NOT NULL,
    "additional_data" jsonb,
    "duration" interval,
    "created_at" timestamp with time zone NOT NULL,
    "moderator_id" bigint NOT NULL,
    "room_id" uuid NOT NULL,
    "target_message_id" uuid,
    "target_user_id" bigint
);

ALTER TABLE "messaging_moderationlog" ADD CONSTRAINT "messaging_moderation_target_message_id_ef9b54a4_fk_messages_" FOREIGN KEY ("target_message_id") REFERENCES "messages" ("id");
ALTER TABLE "messaging_moderationlog" ADD CONSTRAINT "messaging_moderation_target_user_id_1d59ed4b_fk_users_use" FOREIGN KEY ("target_user_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_moderationlog" ADD CONSTRAINT "messaging_moderationlog_moderator_id_55d2ce75_fk_users_user_id" FOREIGN KEY ("moderator_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_moderationlog" ADD CONSTRAINT "messaging_moderationlog_room_id_27d71e50_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_moderationlog" ADD CONSTRAINT "messaging_moderationlog_pkey" PRIMARY KEY ("id");

CREATE INDEX messaging_m_moderat_eb3110_idx ON public.messaging_moderationlog USING btree (moderator_id, created_at);
CREATE INDEX messaging_m_room_id_564178_idx ON public.messaging_moderationlog USING btree (room_id, action_type);
CREATE INDEX messaging_m_target__69a33c_idx ON public.messaging_moderationlog USING btree (target_user_id);
CREATE INDEX messaging_moderationlog_moderator_id_55d2ce75 ON public.messaging_moderationlog USING btree (moderator_id);
CREATE INDEX messaging_moderationlog_room_id_27d71e50 ON public.messaging_moderationlog USING btree (room_id);
CREATE INDEX messaging_moderationlog_target_message_id_ef9b54a4 ON public.messaging_moderationlog USING btree (target_message_id);
CREATE INDEX messaging_moderationlog_target_user_id_1d59ed4b ON public.messaging_moderationlog USING btree (target_user_id);

-- -----------------------------------------------
-- Table: messaging_roombookmark
-- -----------------------------------------------
CREATE TABLE "messaging_roombookmark" (
    "id" uuid NOT NULL,
    "note" text,
    "tags" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "message_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "messaging_roombookmark" ADD CONSTRAINT "messaging_roombookmark_message_id_18bf1f60_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "messaging_roombookmark" ADD CONSTRAINT "messaging_roombookmark_user_id_3b6aab32_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_roombookmark" ADD CONSTRAINT "messaging_roombookmark_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_roombookmark" ADD CONSTRAINT "messaging_roombookmark_user_id_message_id_b5b04fbb_uniq" UNIQUE ("user_id", "message_id");
ALTER TABLE "messaging_roombookmark" ADD CONSTRAINT "messaging_roombookmark_user_id_message_id_b5b04fbb_uniq" UNIQUE ("user_id", "message_id");

CREATE INDEX messaging_roombookmark_message_id_18bf1f60 ON public.messaging_roombookmark USING btree (message_id);
CREATE INDEX messaging_roombookmark_user_id_3b6aab32 ON public.messaging_roombookmark USING btree (user_id);
CREATE UNIQUE INDEX messaging_roombookmark_user_id_message_id_b5b04fbb_uniq ON public.messaging_roombookmark USING btree (user_id, message_id);

-- -----------------------------------------------
-- Table: messaging_roominvitation
-- -----------------------------------------------
CREATE TABLE "messaging_roominvitation" (
    "id" uuid NOT NULL,
    "status" character varying(20) NOT NULL,
    "message" text,
    "expires_at" timestamp with time zone NOT NULL,
    "invited_role" character varying(20) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "responded_at" timestamp with time zone,
    "invited_by_id" bigint NOT NULL,
    "invited_user_id" bigint NOT NULL,
    "room_id" uuid NOT NULL
);

ALTER TABLE "messaging_roominvitation" ADD CONSTRAINT "messaging_roominvita_invited_by_id_2864d4ba_fk_users_use" FOREIGN KEY ("invited_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_roominvitation" ADD CONSTRAINT "messaging_roominvita_invited_user_id_e1ba2bc0_fk_users_use" FOREIGN KEY ("invited_user_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_roominvitation" ADD CONSTRAINT "messaging_roominvitation_room_id_33e8c11f_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_roominvitation" ADD CONSTRAINT "messaging_roominvitation_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_roominvitation" ADD CONSTRAINT "messaging_roominvitation_room_id_invited_user_id_c8b27e61_uniq" UNIQUE ("room_id", "invited_user_id");
ALTER TABLE "messaging_roominvitation" ADD CONSTRAINT "messaging_roominvitation_room_id_invited_user_id_c8b27e61_uniq" UNIQUE ("room_id", "invited_user_id");

CREATE INDEX messaging_r_expires_dc116c_idx ON public.messaging_roominvitation USING btree (expires_at);
CREATE INDEX messaging_r_invited_2207b3_idx ON public.messaging_roominvitation USING btree (invited_user_id, status);
CREATE INDEX messaging_roominvitation_invited_by_id_2864d4ba ON public.messaging_roominvitation USING btree (invited_by_id);
CREATE INDEX messaging_roominvitation_invited_user_id_e1ba2bc0 ON public.messaging_roominvitation USING btree (invited_user_id);
CREATE INDEX messaging_roominvitation_room_id_33e8c11f ON public.messaging_roominvitation USING btree (room_id);
CREATE UNIQUE INDEX messaging_roominvitation_room_id_invited_user_id_c8b27e61_uniq ON public.messaging_roominvitation USING btree (room_id, invited_user_id);

-- -----------------------------------------------
-- Table: messaging_roomsettings
-- -----------------------------------------------
CREATE TABLE "messaging_roomsettings" (
    "id" uuid NOT NULL,
    "notifications_enabled" boolean NOT NULL,
    "sound_enabled" boolean NOT NULL,
    "desktop_notifications" boolean NOT NULL,
    "email_notifications" boolean NOT NULL,
    "push_notifications" boolean NOT NULL,
    "keyword_alerts" jsonb NOT NULL,
    "price_alert_threshold" numeric(10,2),
    "custom_theme" jsonb,
    "message_display_mode" character varying(20) NOT NULL,
    "show_read_receipts" boolean NOT NULL,
    "show_typing_indicator" boolean NOT NULL,
    "show_online_status" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "room_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "messaging_roomsettings" ADD CONSTRAINT "messaging_roomsettings_room_id_0614c2f9_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_roomsettings" ADD CONSTRAINT "messaging_roomsettings_user_id_5b4cfedb_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_roomsettings" ADD CONSTRAINT "messaging_roomsettings_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_roomsettings" ADD CONSTRAINT "messaging_roomsettings_user_id_room_id_56c62e59_uniq" UNIQUE ("user_id", "room_id");
ALTER TABLE "messaging_roomsettings" ADD CONSTRAINT "messaging_roomsettings_user_id_room_id_56c62e59_uniq" UNIQUE ("user_id", "room_id");

CREATE INDEX messaging_roomsettings_room_id_0614c2f9 ON public.messaging_roomsettings USING btree (room_id);
CREATE INDEX messaging_roomsettings_user_id_5b4cfedb ON public.messaging_roomsettings USING btree (user_id);
CREATE UNIQUE INDEX messaging_roomsettings_user_id_room_id_56c62e59_uniq ON public.messaging_roomsettings USING btree (user_id, room_id);

-- -----------------------------------------------
-- Table: messaging_scheduledmessage
-- -----------------------------------------------
CREATE TABLE "messaging_scheduledmessage" (
    "id" uuid NOT NULL,
    "content" text NOT NULL,
    "message_type" character varying(20) NOT NULL,
    "scheduled_for" timestamp with time zone NOT NULL,
    "timezone_name" character varying(50) NOT NULL,
    "is_sent" boolean NOT NULL,
    "sent_at" timestamp with time zone,
    "is_recurring" boolean NOT NULL,
    "recurrence_pattern" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "room_id" uuid NOT NULL,
    "sender_id" bigint NOT NULL,
    "sent_message_id" uuid
);

ALTER TABLE "messaging_scheduledmessage" ADD CONSTRAINT "messaging_scheduledm_sent_message_id_d63f62fd_fk_messages_" FOREIGN KEY ("sent_message_id") REFERENCES "messages" ("id");
ALTER TABLE "messaging_scheduledmessage" ADD CONSTRAINT "messaging_scheduledmessage_room_id_4fa99e2b_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_scheduledmessage" ADD CONSTRAINT "messaging_scheduledmessage_sender_id_20f5b4b9_fk_users_user_id" FOREIGN KEY ("sender_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_scheduledmessage" ADD CONSTRAINT "messaging_scheduledmessage_pkey" PRIMARY KEY ("id");

CREATE INDEX messaging_s_room_id_27acb5_idx ON public.messaging_scheduledmessage USING btree (room_id, sender_id);
CREATE INDEX messaging_s_schedul_a6b429_idx ON public.messaging_scheduledmessage USING btree (scheduled_for, is_sent);
CREATE INDEX messaging_scheduledmessage_room_id_4fa99e2b ON public.messaging_scheduledmessage USING btree (room_id);
CREATE INDEX messaging_scheduledmessage_sender_id_20f5b4b9 ON public.messaging_scheduledmessage USING btree (sender_id);
CREATE INDEX messaging_scheduledmessage_sent_message_id_d63f62fd ON public.messaging_scheduledmessage USING btree (sent_message_id);

-- -----------------------------------------------
-- Table: messaging_userratelimit
-- -----------------------------------------------
CREATE TABLE "messaging_userratelimit" (
    "id" uuid NOT NULL,
    "message_count" integer NOT NULL,
    "window_start" timestamp with time zone NOT NULL,
    "window_duration_minutes" integer NOT NULL,
    "is_rate_limited" boolean NOT NULL,
    "rate_limit_until" timestamp with time zone,
    "violation_count" integer NOT NULL,
    "last_violation" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "room_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "messaging_userratelimit" ADD CONSTRAINT "messaging_userratelimit_room_id_0e823d94_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_userratelimit" ADD CONSTRAINT "messaging_userratelimit_user_id_3d5795e8_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_userratelimit" ADD CONSTRAINT "messaging_userratelimit_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_userratelimit" ADD CONSTRAINT "messaging_userratelimit_user_id_room_id_599623d8_uniq" UNIQUE ("user_id", "room_id");
ALTER TABLE "messaging_userratelimit" ADD CONSTRAINT "messaging_userratelimit_user_id_room_id_599623d8_uniq" UNIQUE ("user_id", "room_id");

CREATE INDEX messaging_userratelimit_room_id_0e823d94 ON public.messaging_userratelimit USING btree (room_id);
CREATE INDEX messaging_userratelimit_user_id_3d5795e8 ON public.messaging_userratelimit USING btree (user_id);
CREATE UNIQUE INDEX messaging_userratelimit_user_id_room_id_599623d8_uniq ON public.messaging_userratelimit USING btree (user_id, room_id);

-- -----------------------------------------------
-- Table: messaging_voicemessage
-- -----------------------------------------------
CREATE TABLE "messaging_voicemessage" (
    "id" uuid NOT NULL,
    "audio_url" character varying(200) NOT NULL,
    "duration_seconds" integer NOT NULL,
    "file_size" bigint NOT NULL,
    "audio_format" character varying(10) NOT NULL,
    "transcription" text,
    "is_transcribed" boolean NOT NULL,
    "processing_status" character varying(20) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "message_id" uuid NOT NULL
);

ALTER TABLE "messaging_voicemessage" ADD CONSTRAINT "messaging_voicemessage_message_id_32c706e0_fk_messages_id" FOREIGN KEY ("message_id") REFERENCES "messages" ("id");
ALTER TABLE "messaging_voicemessage" ADD CONSTRAINT "messaging_voicemessage_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_voicemessage" ADD CONSTRAINT "messaging_voicemessage_message_id_key" UNIQUE ("message_id");

CREATE UNIQUE INDEX messaging_voicemessage_message_id_key ON public.messaging_voicemessage USING btree (message_id);

-- -----------------------------------------------
-- Table: messaging_websocketconnection
-- -----------------------------------------------
CREATE TABLE "messaging_websocketconnection" (
    "id" uuid NOT NULL,
    "connection_id" character varying(255) NOT NULL,
    "device_info" jsonb,
    "ip_address" character varying(45),
    "is_active" boolean NOT NULL,
    "connected_at" timestamp with time zone NOT NULL,
    "last_ping" timestamp with time zone NOT NULL,
    "disconnected_at" timestamp with time zone,
    "user_agent" text,
    "connection_type" character varying(20) NOT NULL,
    "room_id" uuid,
    "user_id" bigint NOT NULL
);

ALTER TABLE "messaging_websocketconnection" ADD CONSTRAINT "messaging_websocketconnection_room_id_02b67ec3_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "messaging_websocketconnection" ADD CONSTRAINT "messaging_websocketconnection_user_id_a6590aef_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "messaging_websocketconnection" ADD CONSTRAINT "messaging_websocketconnection_pkey" PRIMARY KEY ("id");
ALTER TABLE "messaging_websocketconnection" ADD CONSTRAINT "messaging_websocketconnection_connection_id_key" UNIQUE ("connection_id");

CREATE INDEX messaging_w_last_pi_354c1a_idx ON public.messaging_websocketconnection USING btree (last_ping);
CREATE INDEX messaging_w_room_id_c6ae4d_idx ON public.messaging_websocketconnection USING btree (room_id, is_active);
CREATE INDEX messaging_w_user_id_135216_idx ON public.messaging_websocketconnection USING btree (user_id, is_active);
CREATE INDEX messaging_websocketconnection_connection_id_6cde7f00_like ON public.messaging_websocketconnection USING btree (connection_id varchar_pattern_ops);
CREATE UNIQUE INDEX messaging_websocketconnection_connection_id_key ON public.messaging_websocketconnection USING btree (connection_id);
CREATE INDEX messaging_websocketconnection_room_id_02b67ec3 ON public.messaging_websocketconnection USING btree (room_id);
CREATE INDEX messaging_websocketconnection_user_id_a6590aef ON public.messaging_websocketconnection USING btree (user_id);

-- -----------------------------------------------
-- Table: model_metadata
-- -----------------------------------------------
CREATE TABLE "model_metadata" (
    "id" character varying NOT NULL,
    "model_id" character varying NOT NULL,
    "ui_config_version" character varying NOT NULL,
    "ui_config" json,
    "supports_streaming" boolean,
    "supports_function_calling" boolean,
    "max_tokens" integer,
    "temperature_range" json,
    "prompt_fields" json,
    "avg_latency_ms" double precision,
    "avg_tokens_per_second" double precision,
    "accuracy_score" double precision,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone
);

ALTER TABLE "model_metadata" ADD CONSTRAINT "model_metadata_model_id_fkey" FOREIGN KEY ("model_id") REFERENCES "models" ("id");
ALTER TABLE "model_metadata" ADD CONSTRAINT "model_metadata_pkey" PRIMARY KEY ("id");
ALTER TABLE "model_metadata" ADD CONSTRAINT "model_metadata_model_id_key" UNIQUE ("model_id");

CREATE INDEX ix_model_metadata_id ON public.model_metadata USING btree (id);
CREATE UNIQUE INDEX model_metadata_model_id_key ON public.model_metadata USING btree (model_id);

-- -----------------------------------------------
-- Table: model_usage_tracking
-- -----------------------------------------------
CREATE TABLE "model_usage_tracking" (
    "id" uuid NOT NULL,
    "tenant_id" uuid,
    "workspace_id" uuid,
    "user_id" uuid,
    "model_id" character varying(255) NOT NULL,
    "agent_id" character varying(100),
    "input_tokens" bigint NOT NULL,
    "output_tokens" bigint NOT NULL,
    "estimated_cost" numeric(12,6),
    "session_id" character varying(255),
    "created_at" timestamp with time zone NOT NULL,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb
);

ALTER TABLE "model_usage_tracking" ADD CONSTRAINT "model_usage_tracking_pkey" PRIMARY KEY ("id");

CREATE INDEX model_usage_tenant__8cd24e_idx ON public.model_usage_tracking USING btree (tenant_id, created_at);
CREATE INDEX model_usage_tracking_agent_id_28136780 ON public.model_usage_tracking USING btree (agent_id);
CREATE INDEX model_usage_tracking_agent_id_28136780_like ON public.model_usage_tracking USING btree (agent_id varchar_pattern_ops);
CREATE INDEX model_usage_tracking_created_at_f836433c ON public.model_usage_tracking USING btree (created_at);
CREATE INDEX model_usage_tracking_model_id_3aa49f01 ON public.model_usage_tracking USING btree (model_id);
CREATE INDEX model_usage_tracking_model_id_3aa49f01_like ON public.model_usage_tracking USING btree (model_id varchar_pattern_ops);
CREATE INDEX model_usage_tracking_tenant_id_43e44a34 ON public.model_usage_tracking USING btree (tenant_id);
CREATE INDEX model_usage_tracking_user_id_baee374b ON public.model_usage_tracking USING btree (user_id);

-- -----------------------------------------------
-- Table: models
-- -----------------------------------------------
CREATE TABLE "models" (
    "id" character varying NOT NULL,
    "tenant_id" character varying NOT NULL,
    "alias" character varying,
    "model_path" character varying NOT NULL,
    "state" modelstate,
    "version" character varying NOT NULL,
    "description" text,
    "created_by" character varying,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone,
    "deleted_at" timestamp with time zone,
    "is_deleted" boolean
);

ALTER TABLE "models" ADD CONSTRAINT "models_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "tenants" ("id");
ALTER TABLE "models" ADD CONSTRAINT "models_pkey" PRIMARY KEY ("id");

CREATE UNIQUE INDEX ix_models_alias ON public.models USING btree (alias);
CREATE INDEX ix_models_id ON public.models USING btree (id);
CREATE INDEX ix_models_is_deleted ON public.models USING btree (is_deleted);
CREATE INDEX ix_models_state ON public.models USING btree (state);
CREATE INDEX ix_models_tenant_id ON public.models USING btree (tenant_id);

-- -----------------------------------------------
-- Table: network_configurations
-- -----------------------------------------------
CREATE TABLE "network_configurations" (
    "id" uuid NOT NULL,
    "config_type" character varying(50) NOT NULL,
    "configuration" text NOT NULL,
    "description" text NOT NULL,
    "tags" jsonb NOT NULL,
    "metadata" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "session_id" uuid NOT NULL
);

ALTER TABLE "network_configurations" ADD CONSTRAINT "network_configuratio_session_id_82379a63_fk_infrastru" FOREIGN KEY ("session_id") REFERENCES "infrastructure_agentsession" ("id");
ALTER TABLE "network_configurations" ADD CONSTRAINT "network_configurations_pkey" PRIMARY KEY ("id");

CREATE INDEX network_con_config__31a63f_idx ON public.network_configurations USING btree (config_type, created_at);
CREATE INDEX network_con_session_8dc4df_idx ON public.network_configurations USING btree (session_id, config_type);
CREATE INDEX network_configurations_created_at_907af38d ON public.network_configurations USING btree (created_at);
CREATE INDEX network_configurations_session_id_82379a63 ON public.network_configurations USING btree (session_id);

-- -----------------------------------------------
-- Table: notification_categories
-- -----------------------------------------------
CREATE TABLE "notification_categories" (
    "id" uuid NOT NULL,
    "name" character varying(100) NOT NULL,
    "description" text,
    "is_default_enabled" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "ai_generated_content_1" jsonb,
    "ai_generated_content_2" jsonb,
    "reserved_field_1" jsonb
);

ALTER TABLE "notification_categories" ADD CONSTRAINT "notification_categories_pkey" PRIMARY KEY ("id");
ALTER TABLE "notification_categories" ADD CONSTRAINT "notification_categories_name_key" UNIQUE ("name");

CREATE INDEX notification_categories_name_91bfbf06_like ON public.notification_categories USING btree (name varchar_pattern_ops);
CREATE UNIQUE INDEX notification_categories_name_key ON public.notification_categories USING btree (name);

-- -----------------------------------------------
-- Table: notification_channels
-- -----------------------------------------------
CREATE TABLE "notification_channels" (
    "id" uuid NOT NULL,
    "type" character varying(50) NOT NULL,
    "name" character varying(100) NOT NULL,
    "provider" character varying(50) NOT NULL,
    "config" jsonb NOT NULL,
    "priority" integer NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_generated_content_1" jsonb,
    "ai_generated_content_2" jsonb,
    "reserved_field_1" jsonb
);

ALTER TABLE "notification_channels" ADD CONSTRAINT "notification_channels_pkey" PRIMARY KEY ("id");

-- -----------------------------------------------
-- Table: notification_events_log
-- -----------------------------------------------
CREATE TABLE "notification_events_log" (
    "id" uuid NOT NULL,
    "event" character varying(50) NOT NULL,
    "provider_response" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "ai_generated_content_1" jsonb,
    "ai_generated_content_2" jsonb,
    "reserved_field_1" jsonb,
    "notification_id" uuid NOT NULL
);

ALTER TABLE "notification_events_log" ADD CONSTRAINT "notification_events__notification_id_d91ce0af_fk_notificat" FOREIGN KEY ("notification_id") REFERENCES "notifications" ("id");
ALTER TABLE "notification_events_log" ADD CONSTRAINT "notification_events_log_pkey" PRIMARY KEY ("id");

CREATE INDEX notification_events_log_notification_id_d91ce0af ON public.notification_events_log USING btree (notification_id);

-- -----------------------------------------------
-- Table: notification_outbox
-- -----------------------------------------------
CREATE TABLE "notification_outbox" (
    "id" uuid NOT NULL,
    "user_id" uuid NOT NULL,
    "event_type" character varying(50) NOT NULL,
    "aggregate_id" character varying(100),
    "payload" jsonb NOT NULL,
    "priority" smallint NOT NULL,
    "status" character varying(20) NOT NULL,
    "retry_count" integer NOT NULL,
    "max_retries" integer NOT NULL,
    "scheduled_at" timestamp with time zone NOT NULL,
    "processed_at" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "last_error" text,
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_editable_field_1" character varying(64),
    "extended_editable_field_2" character varying(64),
    "extended_editable_field_3" character varying(64),
    "extended_editable_field_4" character varying(64),
    "extended_editable_field_5" character varying(64),
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb
);

ALTER TABLE "notification_outbox" ADD CONSTRAINT "notification_outbox_pkey" PRIMARY KEY ("id");

CREATE INDEX idx_outbox_pending ON public.notification_outbox USING btree (status, scheduled_at) WHERE ((status)::text = 'PENDING'::text);
CREATE INDEX notification_outbox_status_b119d10d ON public.notification_outbox USING btree (status);
CREATE INDEX notification_outbox_status_b119d10d_like ON public.notification_outbox USING btree (status varchar_pattern_ops);

-- -----------------------------------------------
-- Table: notification_preferences
-- -----------------------------------------------
CREATE TABLE "notification_preferences" (
    "id" uuid NOT NULL,
    "username" character varying(255) NOT NULL,
    "organization" character varying(255) NOT NULL,
    "channel_type" character varying(50) NOT NULL,
    "enabled" boolean NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_generated_content_1" jsonb,
    "ai_generated_content_2" jsonb,
    "reserved_field_1" jsonb,
    "category_id" uuid NOT NULL
);

ALTER TABLE "notification_preferences" ADD CONSTRAINT "notification_prefere_category_id_44ed5446_fk_notificat" FOREIGN KEY ("category_id") REFERENCES "notification_categories" ("id");
ALTER TABLE "notification_preferences" ADD CONSTRAINT "notification_preferences_pkey" PRIMARY KEY ("id");
ALTER TABLE "notification_preferences" ADD CONSTRAINT "notification_preferences_username_category_id_cha_c338bf7c_uniq" UNIQUE ("username", "category_id", "channel_type");
ALTER TABLE "notification_preferences" ADD CONSTRAINT "notification_preferences_username_category_id_cha_c338bf7c_uniq" UNIQUE ("username", "category_id", "channel_type");
ALTER TABLE "notification_preferences" ADD CONSTRAINT "notification_preferences_username_category_id_cha_c338bf7c_uniq" UNIQUE ("username", "category_id", "channel_type");

CREATE INDEX notification_preferences_category_id_44ed5446 ON public.notification_preferences USING btree (category_id);
CREATE UNIQUE INDEX notification_preferences_username_category_id_cha_c338bf7c_uniq ON public.notification_preferences USING btree (username, category_id, channel_type);

-- -----------------------------------------------
-- Table: notification_templates
-- -----------------------------------------------
CREATE TABLE "notification_templates" (
    "id" uuid NOT NULL,
    "slug" character varying(100) NOT NULL,
    "channel_type" character varying(50) NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text,
    "subject_template" text,
    "body_template" text NOT NULL,
    "default_data" jsonb NOT NULL,
    "version" character varying(20) NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_generated_content_1" jsonb,
    "ai_generated_content_2" jsonb,
    "reserved_field_1" jsonb
);

ALTER TABLE "notification_templates" ADD CONSTRAINT "notification_templates_pkey" PRIMARY KEY ("id");
ALTER TABLE "notification_templates" ADD CONSTRAINT "notification_templates_slug_channel_type_version_27f78f76_uniq" UNIQUE ("slug", "channel_type", "version");
ALTER TABLE "notification_templates" ADD CONSTRAINT "notification_templates_slug_channel_type_version_27f78f76_uniq" UNIQUE ("slug", "channel_type", "version");
ALTER TABLE "notification_templates" ADD CONSTRAINT "notification_templates_slug_channel_type_version_27f78f76_uniq" UNIQUE ("slug", "channel_type", "version");

CREATE UNIQUE INDEX notification_templates_slug_channel_type_version_27f78f76_uniq ON public.notification_templates USING btree (slug, channel_type, version);

-- -----------------------------------------------
-- Table: notifications
-- -----------------------------------------------
CREATE TABLE "notifications" (
    "id" uuid NOT NULL,
    "tenant_id" character varying(255),
    "organization" character varying(255) NOT NULL,
    "username" character varying(255),
    "recipient" character varying(255) NOT NULL,
    "event_type" character varying(100),
    "entity_type" character varying(100),
    "entity_id" character varying(255),
    "channel_type" character varying(50) NOT NULL,
    "title" character varying(512),
    "body" text,
    "data" jsonb,
    "status" character varying(50) NOT NULL,
    "priority" character varying(20) NOT NULL,
    "retry_count" integer NOT NULL,
    "max_retries" integer NOT NULL,
    "next_retry_at" timestamp with time zone,
    "scheduled_at" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "sent_at" timestamp with time zone,
    "delivered_at" timestamp with time zone,
    "read_at" timestamp with time zone,
    "error_code" character varying(100),
    "error_message" text,
    "ai_generated_content_1" jsonb,
    "ai_generated_content_2" jsonb,
    "reserved_field_1" jsonb,
    "template_id" uuid
);

ALTER TABLE "notifications" ADD CONSTRAINT "notifications_template_id_2988e288_fk_notification_templates_id" FOREIGN KEY ("template_id") REFERENCES "notification_templates" ("id");
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_pkey" PRIMARY KEY ("id");

CREATE INDEX idx_next_retry ON public.notifications USING btree (next_retry_at) WHERE (((status)::text = 'failed'::text) OR ((status)::text = 'queued'::text));
CREATE INDEX notificatio_created_e4c995_idx ON public.notifications USING btree (created_at);
CREATE INDEX notificatio_status_fce6f5_idx ON public.notifications USING btree (status);
CREATE INDEX notificatio_tenant__138085_idx ON public.notifications USING btree (tenant_id, organization);
CREATE INDEX notificatio_usernam_8d8e24_idx ON public.notifications USING btree (username);
CREATE INDEX notifications_created_at_878ec15c ON public.notifications USING btree (created_at);
CREATE INDEX notifications_status_192586aa ON public.notifications USING btree (status);
CREATE INDEX notifications_status_192586aa_like ON public.notifications USING btree (status varchar_pattern_ops);
CREATE INDEX notifications_template_id_2988e288 ON public.notifications USING btree (template_id);

-- -----------------------------------------------
-- Table: oauth_accounts
-- -----------------------------------------------
CREATE TABLE "oauth_accounts" (
    "id" uuid NOT NULL,
    "provider" character varying(20) NOT NULL,
    "provider_user_id" character varying(255) NOT NULL,
    "email" character varying(254),
    "access_token" text,
    "refresh_token" text,
    "token_expires_at" timestamp with time zone,
    "raw_data" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "oauth_accounts" ADD CONSTRAINT "oauth_accounts_user_id_b5b4829c_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "oauth_accounts" ADD CONSTRAINT "oauth_accounts_pkey" PRIMARY KEY ("id");
ALTER TABLE "oauth_accounts" ADD CONSTRAINT "oauth_accounts_provider_provider_user_id_7501737d_uniq" UNIQUE ("provider", "provider_user_id");
ALTER TABLE "oauth_accounts" ADD CONSTRAINT "oauth_accounts_provider_provider_user_id_7501737d_uniq" UNIQUE ("provider", "provider_user_id");

CREATE INDEX oauth_accou_provide_b9f40c_idx ON public.oauth_accounts USING btree (provider, provider_user_id);
CREATE INDEX oauth_accou_user_id_cd9694_idx ON public.oauth_accounts USING btree (user_id, provider);
CREATE UNIQUE INDEX oauth_accounts_provider_provider_user_id_7501737d_uniq ON public.oauth_accounts USING btree (provider, provider_user_id);
CREATE INDEX oauth_accounts_user_id_b5b4829c ON public.oauth_accounts USING btree (user_id);

-- -----------------------------------------------
-- Table: observability_alerts
-- -----------------------------------------------
CREATE TABLE "observability_alerts" (
    "id" uuid NOT NULL,
    "alert_id" character varying(255) NOT NULL,
    "alert_name" character varying(500) NOT NULL,
    "severity" character varying(50) NOT NULL,
    "status" character varying(50) NOT NULL,
    "message" text NOT NULL,
    "service" character varying(255) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    "resolved_at" timestamp with time zone,
    "metadata" jsonb NOT NULL,
    "session_id" uuid NOT NULL,
    "incident_id" uuid
);

ALTER TABLE "observability_alerts" ADD CONSTRAINT "observability_alerts_incident_id_f20b2ecb_fk_observabi" FOREIGN KEY ("incident_id") REFERENCES "observability_incidents" ("id");
ALTER TABLE "observability_alerts" ADD CONSTRAINT "observability_alerts_session_id_26f4693a_fk_infrastru" FOREIGN KEY ("session_id") REFERENCES "infrastructure_agentsession" ("id");
ALTER TABLE "observability_alerts" ADD CONSTRAINT "observability_alerts_pkey" PRIMARY KEY ("id");
ALTER TABLE "observability_alerts" ADD CONSTRAINT "observability_alerts_alert_id_key" UNIQUE ("alert_id");

CREATE INDEX observabili_alert_i_8d65d6_idx ON public.observability_alerts USING btree (alert_id);
CREATE INDEX observabili_service_a27f4e_idx ON public.observability_alerts USING btree (service, status);
CREATE INDEX observabili_session_aa7062_idx ON public.observability_alerts USING btree (session_id, status);
CREATE INDEX observabili_severit_29b5bf_idx ON public.observability_alerts USING btree (severity, status);
CREATE INDEX observability_alerts_alert_id_37c3293e_like ON public.observability_alerts USING btree (alert_id varchar_pattern_ops);
CREATE UNIQUE INDEX observability_alerts_alert_id_key ON public.observability_alerts USING btree (alert_id);
CREATE INDEX observability_alerts_incident_id_f20b2ecb ON public.observability_alerts USING btree (incident_id);
CREATE INDEX observability_alerts_session_id_26f4693a ON public.observability_alerts USING btree (session_id);
CREATE INDEX observability_alerts_timestamp_f19ab96a ON public.observability_alerts USING btree ("timestamp");

-- -----------------------------------------------
-- Table: observability_incidents
-- -----------------------------------------------
CREATE TABLE "observability_incidents" (
    "id" uuid NOT NULL,
    "incident_id" character varying(255) NOT NULL,
    "title" character varying(500) NOT NULL,
    "description" text NOT NULL,
    "severity" character varying(50) NOT NULL,
    "status" character varying(50) NOT NULL,
    "root_cause" text NOT NULL,
    "resolution" text NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    "resolved_at" timestamp with time zone,
    "metadata" jsonb NOT NULL,
    "session_id" uuid NOT NULL
);

ALTER TABLE "observability_incidents" ADD CONSTRAINT "observability_incide_session_id_426809a6_fk_infrastru" FOREIGN KEY ("session_id") REFERENCES "infrastructure_agentsession" ("id");
ALTER TABLE "observability_incidents" ADD CONSTRAINT "observability_incidents_pkey" PRIMARY KEY ("id");
ALTER TABLE "observability_incidents" ADD CONSTRAINT "observability_incidents_incident_id_key" UNIQUE ("incident_id");

CREATE INDEX observabili_inciden_e88317_idx ON public.observability_incidents USING btree (incident_id);
CREATE INDEX observabili_session_9f36c2_idx ON public.observability_incidents USING btree (session_id, status);
CREATE INDEX observabili_severit_b72008_idx ON public.observability_incidents USING btree (severity, status);
CREATE INDEX observability_incidents_incident_id_c5886a3e_like ON public.observability_incidents USING btree (incident_id varchar_pattern_ops);
CREATE UNIQUE INDEX observability_incidents_incident_id_key ON public.observability_incidents USING btree (incident_id);
CREATE INDEX observability_incidents_session_id_426809a6 ON public.observability_incidents USING btree (session_id);
CREATE INDEX observability_incidents_timestamp_ba05d4f3 ON public.observability_incidents USING btree ("timestamp");

-- -----------------------------------------------
-- Table: observability_metrics
-- -----------------------------------------------
CREATE TABLE "observability_metrics" (
    "id" bigint NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "metric_name" character varying(255) NOT NULL,
    "metric_value" double precision NOT NULL,
    "service" character varying(255) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    "metadata" jsonb NOT NULL
);

ALTER TABLE "observability_metrics" ADD CONSTRAINT "observability_metrics_pkey" PRIMARY KEY ("id");

CREATE INDEX observabili_metric__60c3ea_idx ON public.observability_metrics USING btree (metric_name, "timestamp");
CREATE INDEX observabili_session_dd009f_idx ON public.observability_metrics USING btree (session_id, metric_name);
CREATE INDEX observability_metrics_session_id_4a1b7286 ON public.observability_metrics USING btree (session_id);
CREATE INDEX observability_metrics_session_id_4a1b7286_like ON public.observability_metrics USING btree (session_id varchar_pattern_ops);
CREATE INDEX observability_metrics_timestamp_3ac40c1a ON public.observability_metrics USING btree ("timestamp");

-- -----------------------------------------------
-- Table: observability_queries
-- -----------------------------------------------
CREATE TABLE "observability_queries" (
    "id" bigint NOT NULL,
    "session_id" character varying(255) NOT NULL,
    "user_query" text NOT NULL,
    "intent" character varying(100),
    "response" text NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    "metadata" jsonb NOT NULL
);

ALTER TABLE "observability_queries" ADD CONSTRAINT "observability_queries_pkey" PRIMARY KEY ("id");

CREATE INDEX observabili_session_2d56f1_idx ON public.observability_queries USING btree (session_id, "timestamp");
CREATE INDEX observability_queries_session_id_3169f344 ON public.observability_queries USING btree (session_id);
CREATE INDEX observability_queries_session_id_3169f344_like ON public.observability_queries USING btree (session_id varchar_pattern_ops);
CREATE INDEX observability_queries_timestamp_58104df2 ON public.observability_queries USING btree ("timestamp");

-- -----------------------------------------------
-- Table: pipeline_env_vars
-- -----------------------------------------------
CREATE TABLE "pipeline_env_vars" (
    "id" uuid NOT NULL,
    "environment" character varying(50) NOT NULL,
    "key" character varying(255) NOT NULL,
    "value_encrypted" text NOT NULL,
    "is_secret" boolean NOT NULL,
    "description" text NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "pipeline_id" uuid NOT NULL
);

ALTER TABLE "pipeline_env_vars" ADD CONSTRAINT "pipeline_env_vars_pipeline_id_7ebb5586_fk_pipelines_id" FOREIGN KEY ("pipeline_id") REFERENCES "pipelines" ("id");
ALTER TABLE "pipeline_env_vars" ADD CONSTRAINT "pipeline_env_vars_pkey" PRIMARY KEY ("id");
ALTER TABLE "pipeline_env_vars" ADD CONSTRAINT "pipeline_env_vars_pipeline_id_environment_key_d8f414d2_uniq" UNIQUE ("pipeline_id", "environment", "key");
ALTER TABLE "pipeline_env_vars" ADD CONSTRAINT "pipeline_env_vars_pipeline_id_environment_key_d8f414d2_uniq" UNIQUE ("pipeline_id", "environment", "key");
ALTER TABLE "pipeline_env_vars" ADD CONSTRAINT "pipeline_env_vars_pipeline_id_environment_key_d8f414d2_uniq" UNIQUE ("pipeline_id", "environment", "key");

CREATE INDEX pipeline_en_pipelin_ccf104_idx ON public.pipeline_env_vars USING btree (pipeline_id, environment);
CREATE INDEX pipeline_env_vars_created_at_05e0f7f7 ON public.pipeline_env_vars USING btree (created_at);
CREATE INDEX pipeline_env_vars_pipeline_id_7ebb5586 ON public.pipeline_env_vars USING btree (pipeline_id);
CREATE UNIQUE INDEX pipeline_env_vars_pipeline_id_environment_key_d8f414d2_uniq ON public.pipeline_env_vars USING btree (pipeline_id, environment, key);

-- -----------------------------------------------
-- Table: pipeline_history
-- -----------------------------------------------
CREATE TABLE "pipeline_history" (
    "id" uuid NOT NULL,
    "event_type" character varying(50) NOT NULL,
    "event_data" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "build_id" uuid,
    "deployment_id" uuid,
    "pipeline_id" uuid NOT NULL,
    "triggered_by_id" bigint
);

ALTER TABLE "pipeline_history" ADD CONSTRAINT "pipeline_history_build_id_1353acd4_fk_builds_id" FOREIGN KEY ("build_id") REFERENCES "builds" ("id");
ALTER TABLE "pipeline_history" ADD CONSTRAINT "pipeline_history_deployment_id_d945aa16_fk_deployments_id" FOREIGN KEY ("deployment_id") REFERENCES "deployments" ("id");
ALTER TABLE "pipeline_history" ADD CONSTRAINT "pipeline_history_pipeline_id_53e6df81_fk_pipelines_id" FOREIGN KEY ("pipeline_id") REFERENCES "pipelines" ("id");
ALTER TABLE "pipeline_history" ADD CONSTRAINT "pipeline_history_triggered_by_id_511062ec_fk_users_user_id" FOREIGN KEY ("triggered_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "pipeline_history" ADD CONSTRAINT "pipeline_history_pkey" PRIMARY KEY ("id");

CREATE INDEX pipeline_hi_build_i_b9d112_idx ON public.pipeline_history USING btree (build_id);
CREATE INDEX pipeline_hi_created_10e701_idx ON public.pipeline_history USING btree (created_at);
CREATE INDEX pipeline_hi_deploym_3d593a_idx ON public.pipeline_history USING btree (deployment_id);
CREATE INDEX pipeline_hi_pipelin_4f6460_idx ON public.pipeline_history USING btree (pipeline_id, event_type);
CREATE INDEX pipeline_history_build_id_1353acd4 ON public.pipeline_history USING btree (build_id);
CREATE INDEX pipeline_history_created_at_9586bfe7 ON public.pipeline_history USING btree (created_at);
CREATE INDEX pipeline_history_deployment_id_d945aa16 ON public.pipeline_history USING btree (deployment_id);
CREATE INDEX pipeline_history_pipeline_id_53e6df81 ON public.pipeline_history USING btree (pipeline_id);
CREATE INDEX pipeline_history_triggered_by_id_511062ec ON public.pipeline_history USING btree (triggered_by_id);

-- -----------------------------------------------
-- Table: pipelines
-- -----------------------------------------------
CREATE TABLE "pipelines" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text NOT NULL,
    "provider" character varying(50) NOT NULL,
    "repository_url" character varying(500) NOT NULL,
    "repository_id" character varying(255) NOT NULL,
    "branch" character varying(255) NOT NULL,
    "framework" character varying(100) NOT NULL,
    "runtime" character varying(50) NOT NULL,
    "runtime_version" character varying(50) NOT NULL,
    "build_command" text NOT NULL,
    "install_command" text NOT NULL,
    "start_command" text NOT NULL,
    "build_output_dir" character varying(255) NOT NULL,
    "root_directory" character varying(255) NOT NULL,
    "status" character varying(50) NOT NULL,
    "config" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "organization_id" uuid,
    "user_id" bigint NOT NULL
);

ALTER TABLE "pipelines" ADD CONSTRAINT "pipelines_organization_id_d45d3e11_fk_users_organization_id" FOREIGN KEY ("organization_id") REFERENCES "users_organization" ("id");
ALTER TABLE "pipelines" ADD CONSTRAINT "pipelines_user_id_82532f8b_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "pipelines" ADD CONSTRAINT "pipelines_pkey" PRIMARY KEY ("id");
ALTER TABLE "pipelines" ADD CONSTRAINT "pipelines_user_id_name_f3f2b23d_uniq" UNIQUE ("user_id", "name");
ALTER TABLE "pipelines" ADD CONSTRAINT "pipelines_user_id_name_f3f2b23d_uniq" UNIQUE ("user_id", "name");

CREATE INDEX pipelines_created_at_619d5575 ON public.pipelines USING btree (created_at);
CREATE INDEX pipelines_name_6b744a71 ON public.pipelines USING btree (name);
CREATE INDEX pipelines_name_6b744a71_like ON public.pipelines USING btree (name varchar_pattern_ops);
CREATE INDEX pipelines_organiz_7d0ccf_idx ON public.pipelines USING btree (organization_id, status);
CREATE INDEX pipelines_organization_id_d45d3e11 ON public.pipelines USING btree (organization_id);
CREATE INDEX pipelines_provide_d08a49_idx ON public.pipelines USING btree (provider, repository_id);
CREATE INDEX pipelines_repository_id_06fe0932 ON public.pipelines USING btree (repository_id);
CREATE INDEX pipelines_repository_id_06fe0932_like ON public.pipelines USING btree (repository_id varchar_pattern_ops);
CREATE INDEX pipelines_user_id_5c219e_idx ON public.pipelines USING btree (user_id, status);
CREATE INDEX pipelines_user_id_82532f8b ON public.pipelines USING btree (user_id);
CREATE UNIQUE INDEX pipelines_user_id_name_f3f2b23d_uniq ON public.pipelines USING btree (user_id, name);

-- -----------------------------------------------
-- Table: project_collaborators
-- -----------------------------------------------
CREATE TABLE "project_collaborators" (
    "id" uuid NOT NULL,
    "role" character varying(50) NOT NULL,
    "joined_at" timestamp with time zone NOT NULL,
    "extended_editable_field_1" character varying(255),
    "extended_json_field_1" jsonb,
    "user_id" bigint NOT NULL,
    "project_id" uuid NOT NULL
);

ALTER TABLE "project_collaborators" ADD CONSTRAINT "project_collaborators_project_id_0cfa33b4_fk_studio_projects_id" FOREIGN KEY ("project_id") REFERENCES "studio_projects" ("id");
ALTER TABLE "project_collaborators" ADD CONSTRAINT "project_collaborators_user_id_6b261aed_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "project_collaborators" ADD CONSTRAINT "project_collaborators_pkey" PRIMARY KEY ("id");
ALTER TABLE "project_collaborators" ADD CONSTRAINT "project_collaborators_project_id_user_id_883af4c0_uniq" UNIQUE ("project_id", "user_id");
ALTER TABLE "project_collaborators" ADD CONSTRAINT "project_collaborators_project_id_user_id_883af4c0_uniq" UNIQUE ("project_id", "user_id");

CREATE INDEX project_collaborators_project_id_0cfa33b4 ON public.project_collaborators USING btree (project_id);
CREATE UNIQUE INDEX project_collaborators_project_id_user_id_883af4c0_uniq ON public.project_collaborators USING btree (project_id, user_id);
CREATE INDEX project_collaborators_user_id_6b261aed ON public.project_collaborators USING btree (user_id);

-- -----------------------------------------------
-- Table: queue_messages
-- -----------------------------------------------
CREATE TABLE "queue_messages" (
    "id" bigint NOT NULL,
    "owner_user_id" character varying(255),
    "queue_name" character varying(255) NOT NULL,
    "is_fifo" boolean NOT NULL,
    "message_body" jsonb NOT NULL,
    "deduplication_id" character varying(255),
    "group_id" character varying(255),
    "status" character varying(30) NOT NULL,
    "delay_until" timestamp with time zone,
    "visibility_until" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "receive_count" integer NOT NULL,
    "max_receive_count" integer NOT NULL,
    "locked_by" character varying(255),
    "locked_at" timestamp with time zone,
    "extended_editable_field_1" character varying(64),
    "extended_editable_field_2" character varying(64),
    "extended_editable_field_3" character varying(64),
    "extended_editable_field_4" character varying(64),
    "extended_editable_field_5" character varying(64),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb
);

ALTER TABLE "queue_messages" ADD CONSTRAINT "queue_messages_pkey" PRIMARY KEY ("id");

CREATE INDEX queue_messa_created_91773a_idx ON public.queue_messages USING btree (created_at);
CREATE INDEX queue_messa_owner_u_6891dc_idx ON public.queue_messages USING btree (owner_user_id, queue_name);
CREATE INDEX queue_messa_queue_n_9fe5bd_idx ON public.queue_messages USING btree (queue_name, status);
CREATE INDEX queue_messages_owner_user_id_44361684 ON public.queue_messages USING btree (owner_user_id);
CREATE INDEX queue_messages_owner_user_id_44361684_like ON public.queue_messages USING btree (owner_user_id varchar_pattern_ops);

-- -----------------------------------------------
-- Table: request_logs
-- -----------------------------------------------
CREATE TABLE "request_logs" (
    "id" character varying NOT NULL,
    "request_id" character varying NOT NULL,
    "tenant_id" character varying NOT NULL,
    "model_id" character varying,
    "endpoint" character varying NOT NULL,
    "method" character varying NOT NULL,
    "query" text,
    "prompt" text,
    "response" text,
    "tokens_used" integer,
    "tokens_input" integer,
    "tokens_output" integer,
    "latency_ms" double precision,
    "status_code" integer,
    "log_metadata" json,
    "created_at" timestamp with time zone DEFAULT now()
);

ALTER TABLE "request_logs" ADD CONSTRAINT "request_logs_model_id_fkey" FOREIGN KEY ("model_id") REFERENCES "models" ("id");
ALTER TABLE "request_logs" ADD CONSTRAINT "request_logs_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "tenants" ("id");
ALTER TABLE "request_logs" ADD CONSTRAINT "request_logs_pkey" PRIMARY KEY ("id");

CREATE INDEX ix_request_logs_created_at ON public.request_logs USING btree (created_at);
CREATE INDEX ix_request_logs_id ON public.request_logs USING btree (id);
CREATE INDEX ix_request_logs_model_id ON public.request_logs USING btree (model_id);
CREATE UNIQUE INDEX ix_request_logs_request_id ON public.request_logs USING btree (request_id);
CREATE INDEX ix_request_logs_tenant_id ON public.request_logs USING btree (tenant_id);

-- -----------------------------------------------
-- Table: sales_follow_up
-- -----------------------------------------------
CREATE TABLE "sales_follow_up" (
    "id" integer NOT NULL,
    "lead_email" character varying(254),
    "business_name" character varying(255),
    "sales_rep_name" character varying(255),
    "follow_up_history" jsonb NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb,
    "lead_id" integer NOT NULL,
    "sales_rep_id" integer
);

ALTER TABLE "sales_follow_up" ADD CONSTRAINT "sales_follow_up_lead_id_7b8aa2b0_fk_leads_id" FOREIGN KEY ("lead_id") REFERENCES "leads" ("id");
ALTER TABLE "sales_follow_up" ADD CONSTRAINT "sales_follow_up_sales_rep_id_701743bc_fk_sales_rep" FOREIGN KEY ("sales_rep_id") REFERENCES "sales_representatives" ("id");
ALTER TABLE "sales_follow_up" ADD CONSTRAINT "sales_follow_up_pkey" PRIMARY KEY ("id");

CREATE INDEX idx_follow_up_business_name ON public.sales_follow_up USING btree (business_name);
CREATE INDEX idx_follow_up_created_at ON public.sales_follow_up USING btree (created_at);
CREATE INDEX idx_follow_up_lead_email ON public.sales_follow_up USING btree (lead_email);
CREATE INDEX idx_follow_up_lead_id ON public.sales_follow_up USING btree (lead_id);
CREATE INDEX idx_follow_up_sales_rep_id ON public.sales_follow_up USING btree (sales_rep_id);
CREATE INDEX sales_follow_up_lead_id_7b8aa2b0 ON public.sales_follow_up USING btree (lead_id);
CREATE INDEX sales_follow_up_sales_rep_id_701743bc ON public.sales_follow_up USING btree (sales_rep_id);

-- -----------------------------------------------
-- Table: sales_representatives
-- -----------------------------------------------
CREATE TABLE "sales_representatives" (
    "id" integer NOT NULL,
    "name" character varying(255) NOT NULL,
    "email" character varying(254),
    "phone_number" character varying(50),
    "active" boolean NOT NULL,
    "total_leads" integer NOT NULL,
    "total_calls" integer NOT NULL,
    "total_meetings_booked" integer NOT NULL,
    "total_deals_closed" integer NOT NULL,
    "total_revenue" numeric(12,2) NOT NULL,
    "notes" text NOT NULL,
    "commission_rate" numeric(5,2) NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "reserved_field_1" text,
    "reserved_field_2" text,
    "reserved_field_boolean" boolean NOT NULL,
    "reserved_field_json_1" jsonb,
    "reserved_field_json_2" jsonb
);

ALTER TABLE "sales_representatives" ADD CONSTRAINT "sales_representatives_pkey" PRIMARY KEY ("id");
ALTER TABLE "sales_representatives" ADD CONSTRAINT "sales_representatives_email_key" UNIQUE ("email");

CREATE INDEX idx_sales_rep_active ON public.sales_representatives USING btree (active);
CREATE INDEX idx_sales_rep_email ON public.sales_representatives USING btree (email);
CREATE INDEX idx_sales_rep_name ON public.sales_representatives USING btree (name);
CREATE INDEX sales_representatives_email_54edb143_like ON public.sales_representatives USING btree (email varchar_pattern_ops);
CREATE UNIQUE INDEX sales_representatives_email_key ON public.sales_representatives USING btree (email);

-- -----------------------------------------------
-- Table: studio_projects
-- -----------------------------------------------
CREATE TABLE "studio_projects" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "storage_path" character varying(512) NOT NULL,
    "runtime_type" character varying(100) NOT NULL,
    "is_template" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "git_repository_id" uuid,
    "owner_id" bigint NOT NULL,
    "workspace_id" uuid
);

ALTER TABLE "studio_projects" ADD CONSTRAINT "studio_projects_git_repository_id_68c5299d_fk_git_repos" FOREIGN KEY ("git_repository_id") REFERENCES "git_repositories" ("id");
ALTER TABLE "studio_projects" ADD CONSTRAINT "studio_projects_owner_id_7e8921e3_fk_users_user_id" FOREIGN KEY ("owner_id") REFERENCES "users_user" ("id");
ALTER TABLE "studio_projects" ADD CONSTRAINT "studio_projects_workspace_id_678bfccf_fk_infrastru" FOREIGN KEY ("workspace_id") REFERENCES "infrastructure_workspace" ("id");
ALTER TABLE "studio_projects" ADD CONSTRAINT "studio_projects_pkey" PRIMARY KEY ("id");

CREATE INDEX studio_proj_owner_i_d9272a_idx ON public.studio_projects USING btree (owner_id, name);
CREATE INDEX studio_proj_workspa_e148a9_idx ON public.studio_projects USING btree (workspace_id);
CREATE INDEX studio_projects_created_at_c6443e5c ON public.studio_projects USING btree (created_at);
CREATE INDEX studio_projects_git_repository_id_68c5299d ON public.studio_projects USING btree (git_repository_id);
CREATE INDEX studio_projects_owner_id_7e8921e3 ON public.studio_projects USING btree (owner_id);
CREATE INDEX studio_projects_workspace_id_678bfccf ON public.studio_projects USING btree (workspace_id);

-- -----------------------------------------------
-- Table: studio_runtimes
-- -----------------------------------------------
CREATE TABLE "studio_runtimes" (
    "id" uuid NOT NULL,
    "container_id" character varying(255),
    "subdomain" character varying(255),
    "status" character varying(50) NOT NULL,
    "port_mapping" jsonb NOT NULL,
    "cpu_limit" double precision NOT NULL,
    "memory_limit_mb" integer NOT NULL,
    "last_heartbeat" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "project_id" uuid NOT NULL
);

ALTER TABLE "studio_runtimes" ADD CONSTRAINT "studio_runtimes_project_id_aee5e145_fk_studio_projects_id" FOREIGN KEY ("project_id") REFERENCES "studio_projects" ("id");
ALTER TABLE "studio_runtimes" ADD CONSTRAINT "studio_runtimes_pkey" PRIMARY KEY ("id");
ALTER TABLE "studio_runtimes" ADD CONSTRAINT "studio_runtimes_project_id_key" UNIQUE ("project_id");
ALTER TABLE "studio_runtimes" ADD CONSTRAINT "studio_runtimes_subdomain_key" UNIQUE ("subdomain");

CREATE UNIQUE INDEX studio_runtimes_project_id_key ON public.studio_runtimes USING btree (project_id);
CREATE INDEX studio_runtimes_subdomain_ec5f130b_like ON public.studio_runtimes USING btree (subdomain varchar_pattern_ops);
CREATE UNIQUE INDEX studio_runtimes_subdomain_key ON public.studio_runtimes USING btree (subdomain);

-- -----------------------------------------------
-- Table: subscriptions_invoice
-- -----------------------------------------------
CREATE TABLE "subscriptions_invoice" (
    "id" uuid NOT NULL,
    "amount" numeric(10,2) NOT NULL,
    "currency" character varying(3) NOT NULL,
    "period_start" timestamp with time zone NOT NULL,
    "period_end" timestamp with time zone NOT NULL,
    "issued_at" timestamp with time zone NOT NULL,
    "due_date" timestamp with time zone NOT NULL,
    "status" character varying(20) NOT NULL,
    "pdf_url" character varying(200),
    "provider_invoice_id" character varying(255),
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "subscription_id" uuid NOT NULL
);

ALTER TABLE "subscriptions_invoice" ADD CONSTRAINT "subscriptions_invoic_subscription_id_c4ac2071_fk_subscript" FOREIGN KEY ("subscription_id") REFERENCES "subscriptions_usersubscription" ("id");
ALTER TABLE "subscriptions_invoice" ADD CONSTRAINT "subscriptions_invoice_pkey" PRIMARY KEY ("id");

CREATE INDEX subscriptions_invoice_subscription_id_c4ac2071 ON public.subscriptions_invoice USING btree (subscription_id);

-- -----------------------------------------------
-- Table: subscriptions_invoiceplanning
-- -----------------------------------------------
CREATE TABLE "subscriptions_invoiceplanning" (
    "id" uuid NOT NULL,
    "amount" numeric(10,2) NOT NULL,
    "currency" character varying(3) NOT NULL,
    "period_start" timestamp with time zone NOT NULL,
    "period_end" timestamp with time zone NOT NULL,
    "scheduled_for" timestamp with time zone NOT NULL,
    "status" character varying(20) NOT NULL,
    "metadata" jsonb,
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "plan_id" uuid NOT NULL,
    "subscription_id" uuid NOT NULL
);

ALTER TABLE "subscriptions_invoiceplanning" ADD CONSTRAINT "subscriptions_invoic_plan_id_094e901f_fk_subscript" FOREIGN KEY ("plan_id") REFERENCES "subscriptions_subscriptionplan" ("id");
ALTER TABLE "subscriptions_invoiceplanning" ADD CONSTRAINT "subscriptions_invoic_subscription_id_93559f34_fk_subscript" FOREIGN KEY ("subscription_id") REFERENCES "subscriptions_usersubscription" ("id");
ALTER TABLE "subscriptions_invoiceplanning" ADD CONSTRAINT "subscriptions_invoiceplanning_pkey" PRIMARY KEY ("id");

CREATE INDEX subscriptions_invoiceplanning_plan_id_094e901f ON public.subscriptions_invoiceplanning USING btree (plan_id);
CREATE INDEX subscriptions_invoiceplanning_subscription_id_93559f34 ON public.subscriptions_invoiceplanning USING btree (subscription_id);

-- -----------------------------------------------
-- Table: subscriptions_payment
-- -----------------------------------------------
CREATE TABLE "subscriptions_payment" (
    "id" uuid NOT NULL,
    "amount" numeric(10,2) NOT NULL,
    "currency" character varying(3) NOT NULL,
    "provider_transaction_id" character varying(255) NOT NULL,
    "payment_method" character varying(50) NOT NULL,
    "status" character varying(20) NOT NULL,
    "paid_at" timestamp with time zone,
    "failure_reason" text,
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "invoice_id" uuid NOT NULL
);

ALTER TABLE "subscriptions_payment" ADD CONSTRAINT "subscriptions_paymen_invoice_id_f0a97ee0_fk_subscript" FOREIGN KEY ("invoice_id") REFERENCES "subscriptions_invoice" ("id");
ALTER TABLE "subscriptions_payment" ADD CONSTRAINT "subscriptions_payment_pkey" PRIMARY KEY ("id");
ALTER TABLE "subscriptions_payment" ADD CONSTRAINT "subscriptions_payment_invoice_id_key" UNIQUE ("invoice_id");
ALTER TABLE "subscriptions_payment" ADD CONSTRAINT "subscriptions_payment_provider_transaction_id_key" UNIQUE ("provider_transaction_id");

CREATE UNIQUE INDEX subscriptions_payment_invoice_id_key ON public.subscriptions_payment USING btree (invoice_id);
CREATE INDEX subscriptions_payment_provider_transaction_id_27f09f7f_like ON public.subscriptions_payment USING btree (provider_transaction_id varchar_pattern_ops);
CREATE UNIQUE INDEX subscriptions_payment_provider_transaction_id_key ON public.subscriptions_payment USING btree (provider_transaction_id);

-- -----------------------------------------------
-- Table: subscriptions_product
-- -----------------------------------------------
CREATE TABLE "subscriptions_product" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text,
    "short_description" character varying(300) NOT NULL,
    "sku" character varying(100) NOT NULL,
    "product_type" character varying(30) NOT NULL,
    "category" character varying(100) NOT NULL,
    "image" character varying(100),
    "url" character varying(200),
    "features" jsonb,
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "is_active" boolean NOT NULL,
    "metadata" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL
);

ALTER TABLE "subscriptions_product" ADD CONSTRAINT "subscriptions_product_pkey" PRIMARY KEY ("id");

-- -----------------------------------------------
-- Table: subscriptions_serviceaccount
-- -----------------------------------------------
CREATE TABLE "subscriptions_serviceaccount" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "is_active" boolean NOT NULL,
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "subscriptions_serviceaccount" ADD CONSTRAINT "subscriptions_serviceaccount_user_id_ecc1297e_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "subscriptions_serviceaccount" ADD CONSTRAINT "subscriptions_serviceaccount_pkey" PRIMARY KEY ("id");

CREATE INDEX subscriptions_serviceaccount_user_id_ecc1297e ON public.subscriptions_serviceaccount USING btree (user_id);

-- -----------------------------------------------
-- Table: subscriptions_subscriptionplan
-- -----------------------------------------------
CREATE TABLE "subscriptions_subscriptionplan" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "desc" text,
    "price" numeric(59,2) NOT NULL,
    "active" boolean NOT NULL,
    "thumbnail" character varying(255),
    "tags" jsonb,
    "quantity" integer,
    "provider_product_id" character varying(255) NOT NULL,
    "provider_price_id" character varying(255) NOT NULL,
    "metadata" jsonb,
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_market_analysis" jsonb,
    "ai_pricing_recommendations" jsonb,
    "ai_feature_suggestions" jsonb,
    "ai_plan_acceptance_rate" numeric(5,2),
    "ai_plan_modification_details" jsonb,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb
);

ALTER TABLE "subscriptions_subscriptionplan" ADD CONSTRAINT "subscriptions_subscriptionplan_pkey" PRIMARY KEY ("id");
ALTER TABLE "subscriptions_subscriptionplan" ADD CONSTRAINT "subscriptions_subscriptionplan_provider_price_id_key" UNIQUE ("provider_price_id");
ALTER TABLE "subscriptions_subscriptionplan" ADD CONSTRAINT "subscriptions_subscriptionplan_provider_product_id_key" UNIQUE ("provider_product_id");

CREATE INDEX subscriptions_subscripti_provider_product_id_be0377b4_like ON public.subscriptions_subscriptionplan USING btree (provider_product_id varchar_pattern_ops);
CREATE INDEX subscriptions_subscriptionplan_provider_price_id_54ae3dd3_like ON public.subscriptions_subscriptionplan USING btree (provider_price_id varchar_pattern_ops);
CREATE UNIQUE INDEX subscriptions_subscriptionplan_provider_price_id_key ON public.subscriptions_subscriptionplan USING btree (provider_price_id);
CREATE UNIQUE INDEX subscriptions_subscriptionplan_provider_product_id_key ON public.subscriptions_subscriptionplan USING btree (provider_product_id);

-- -----------------------------------------------
-- Table: subscriptions_subscriptiontransaction
-- -----------------------------------------------
CREATE TABLE "subscriptions_subscriptiontransaction" (
    "id" uuid NOT NULL,
    "status" character varying(20) NOT NULL,
    "provider_transaction_id" character varying(255),
    "amount" numeric(10,2) NOT NULL,
    "currency" character varying(10) NOT NULL,
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_fraud_score" numeric(5,2),
    "ai_risk_factors" jsonb,
    "ai_transaction_outcome_prediction" character varying(50),
    "ai_recommendation_action" character varying(50),
    "user_action_on_ai_recommendation" character varying(50),
    "ai_anomaly_detected" boolean NOT NULL,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "plan_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "subscriptions_subscriptiontransaction" ADD CONSTRAINT "subscriptions_subscr_plan_id_e451610f_fk_subscript" FOREIGN KEY ("plan_id") REFERENCES "subscriptions_subscriptionplan" ("id");
ALTER TABLE "subscriptions_subscriptiontransaction" ADD CONSTRAINT "subscriptions_subscr_user_id_a38f7b3a_fk_users_use" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "subscriptions_subscriptiontransaction" ADD CONSTRAINT "subscriptions_subscriptiontransaction_pkey" PRIMARY KEY ("id");

CREATE INDEX subscriptions_subscriptiontransaction_plan_id_e451610f ON public.subscriptions_subscriptiontransaction USING btree (plan_id);
CREATE INDEX subscriptions_subscriptiontransaction_user_id_a38f7b3a ON public.subscriptions_subscriptiontransaction USING btree (user_id);

-- -----------------------------------------------
-- Table: subscriptions_usersubscription
-- -----------------------------------------------
CREATE TABLE "subscriptions_usersubscription" (
    "id" uuid NOT NULL,
    "status" character varying(20) NOT NULL,
    "auto_renew" boolean NOT NULL,
    "trial_end_date" timestamp with time zone,
    "current_period_start" timestamp with time zone NOT NULL,
    "current_period_end" timestamp with time zone NOT NULL,
    "seo" jsonb,
    "keywords" jsonb,
    "ai_fields" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb,
    "plan_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "subscriptions_usersubscription" ADD CONSTRAINT "subscriptions_usersu_plan_id_553a4857_fk_subscript" FOREIGN KEY ("plan_id") REFERENCES "subscriptions_subscriptionplan" ("id");
ALTER TABLE "subscriptions_usersubscription" ADD CONSTRAINT "subscriptions_usersu_user_id_fd3f47a9_fk_users_use" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "subscriptions_usersubscription" ADD CONSTRAINT "subscriptions_usersubscription_pkey" PRIMARY KEY ("id");

CREATE INDEX subscriptions_usersubscription_plan_id_553a4857 ON public.subscriptions_usersubscription USING btree (plan_id);
CREATE INDEX subscriptions_usersubscription_user_id_fd3f47a9 ON public.subscriptions_usersubscription USING btree (user_id);

-- -----------------------------------------------
-- Table: templates
-- -----------------------------------------------
CREATE TABLE "templates" (
    "id" uuid NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" text NOT NULL,
    "framework" character varying(100) NOT NULL,
    "category" character varying(100) NOT NULL,
    "repository_url" character varying(500) NOT NULL,
    "preview_image_url" character varying(500) NOT NULL,
    "documentation_url" character varying(500) NOT NULL,
    "config_schema" jsonb NOT NULL,
    "default_config" jsonb NOT NULL,
    "tags" jsonb NOT NULL,
    "is_public" boolean NOT NULL,
    "usage_count" integer NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "created_by_id" bigint
);

ALTER TABLE "templates" ADD CONSTRAINT "templates_created_by_id_fb9906ed_fk_users_user_id" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");
ALTER TABLE "templates" ADD CONSTRAINT "templates_pkey" PRIMARY KEY ("id");
ALTER TABLE "templates" ADD CONSTRAINT "templates_name_key" UNIQUE ("name");

CREATE INDEX templates_created_at_6b43e3e7 ON public.templates USING btree (created_at);
CREATE INDEX templates_created_by_id_fb9906ed ON public.templates USING btree (created_by_id);
CREATE INDEX templates_framewo_53b808_idx ON public.templates USING btree (framework, category);
CREATE INDEX templates_is_publ_c33849_idx ON public.templates USING btree (is_public);
CREATE INDEX templates_name_74140bc0_like ON public.templates USING btree (name varchar_pattern_ops);
CREATE UNIQUE INDEX templates_name_key ON public.templates USING btree (name);

-- -----------------------------------------------
-- Table: tenant_model_preferences
-- -----------------------------------------------
CREATE TABLE "tenant_model_preferences" (
    "id" uuid NOT NULL,
    "tenant_id" uuid,
    "workspace_id" uuid,
    "agent_id" character varying(100) NOT NULL,
    "model_id" character varying(255) NOT NULL,
    "priority" integer NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb
);

ALTER TABLE "tenant_model_preferences" ADD CONSTRAINT "tenant_model_preferences_pkey" PRIMARY KEY ("id");

CREATE INDEX tenant_mode_tenant__29685a_idx ON public.tenant_model_preferences USING btree (tenant_id, workspace_id, agent_id);
CREATE INDEX tenant_model_preferences_agent_id_d2aba5ff ON public.tenant_model_preferences USING btree (agent_id);
CREATE INDEX tenant_model_preferences_agent_id_d2aba5ff_like ON public.tenant_model_preferences USING btree (agent_id varchar_pattern_ops);
CREATE INDEX tenant_model_preferences_model_id_a2abf4ec ON public.tenant_model_preferences USING btree (model_id);
CREATE INDEX tenant_model_preferences_model_id_a2abf4ec_like ON public.tenant_model_preferences USING btree (model_id varchar_pattern_ops);
CREATE INDEX tenant_model_preferences_tenant_id_284a26bb ON public.tenant_model_preferences USING btree (tenant_id);

-- -----------------------------------------------
-- Table: tenants
-- -----------------------------------------------
CREATE TABLE "tenants" (
    "id" character varying NOT NULL,
    "name" character varying NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone,
    "is_active" boolean,
    "tpm_limit" integer,
    "rpm_limit" integer
);

ALTER TABLE "tenants" ADD CONSTRAINT "tenants_pkey" PRIMARY KEY ("id");

CREATE INDEX ix_tenants_id ON public.tenants USING btree (id);

-- -----------------------------------------------
-- Table: token_blacklist_blacklistedtoken
-- -----------------------------------------------
CREATE TABLE "token_blacklist_blacklistedtoken" (
    "id" bigint NOT NULL,
    "blacklisted_at" timestamp with time zone NOT NULL,
    "token_id" bigint NOT NULL
);

ALTER TABLE "token_blacklist_blacklistedtoken" ADD CONSTRAINT "token_blacklist_blacklistedtoken_token_id_3cc7fe56_fk" FOREIGN KEY ("token_id") REFERENCES "token_blacklist_outstandingtoken" ("id");
ALTER TABLE "token_blacklist_blacklistedtoken" ADD CONSTRAINT "token_blacklist_blacklistedtoken_pkey" PRIMARY KEY ("id");
ALTER TABLE "token_blacklist_blacklistedtoken" ADD CONSTRAINT "token_blacklist_blacklistedtoken_token_id_key" UNIQUE ("token_id");

CREATE UNIQUE INDEX token_blacklist_blacklistedtoken_token_id_key ON public.token_blacklist_blacklistedtoken USING btree (token_id);

-- -----------------------------------------------
-- Table: token_blacklist_outstandingtoken
-- -----------------------------------------------
CREATE TABLE "token_blacklist_outstandingtoken" (
    "id" bigint NOT NULL,
    "token" text NOT NULL,
    "created_at" timestamp with time zone,
    "expires_at" timestamp with time zone NOT NULL,
    "user_id" bigint,
    "jti" character varying(255) NOT NULL
);

ALTER TABLE "token_blacklist_outstandingtoken" ADD CONSTRAINT "token_blacklist_outs_user_id_83bc629a_fk_users_use" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "token_blacklist_outstandingtoken" ADD CONSTRAINT "token_blacklist_outstandingtoken_pkey" PRIMARY KEY ("id");
ALTER TABLE "token_blacklist_outstandingtoken" ADD CONSTRAINT "token_blacklist_outstandingtoken_jti_hex_d9bdf6f7_uniq" UNIQUE ("jti");

CREATE INDEX token_blacklist_outstandingtoken_jti_hex_d9bdf6f7_like ON public.token_blacklist_outstandingtoken USING btree (jti varchar_pattern_ops);
CREATE UNIQUE INDEX token_blacklist_outstandingtoken_jti_hex_d9bdf6f7_uniq ON public.token_blacklist_outstandingtoken USING btree (jti);
CREATE INDEX token_blacklist_outstandingtoken_user_id_83bc629a ON public.token_blacklist_outstandingtoken USING btree (user_id);

-- -----------------------------------------------
-- Table: typing_indicators
-- -----------------------------------------------
CREATE TABLE "typing_indicators" (
    "id" uuid NOT NULL,
    "is_typing" boolean NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "started_at" timestamp with time zone NOT NULL,
    "room_id" uuid NOT NULL,
    "user_id" bigint NOT NULL
);

ALTER TABLE "typing_indicators" ADD CONSTRAINT "typing_indicators_room_id_3137d767_fk_chat_rooms_id" FOREIGN KEY ("room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "typing_indicators" ADD CONSTRAINT "typing_indicators_user_id_025736ca_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "typing_indicators" ADD CONSTRAINT "typing_indicators_pkey" PRIMARY KEY ("id");
ALTER TABLE "typing_indicators" ADD CONSTRAINT "typing_indicators_room_id_user_id_9b475b33_uniq" UNIQUE ("room_id", "user_id");
ALTER TABLE "typing_indicators" ADD CONSTRAINT "typing_indicators_room_id_user_id_9b475b33_uniq" UNIQUE ("room_id", "user_id");

CREATE INDEX typing_indicators_room_id_3137d767 ON public.typing_indicators USING btree (room_id);
CREATE UNIQUE INDEX typing_indicators_room_id_user_id_9b475b33_uniq ON public.typing_indicators USING btree (room_id, user_id);
CREATE INDEX typing_indicators_user_id_025736ca ON public.typing_indicators USING btree (user_id);

-- -----------------------------------------------
-- Table: user_presence
-- -----------------------------------------------
CREATE TABLE "user_presence" (
    "user_id" bigint NOT NULL,
    "status" character varying(20) NOT NULL,
    "status_message" character varying(200),
    "last_activity" timestamp with time zone NOT NULL,
    "last_seen" timestamp with time zone NOT NULL,
    "last_seen_ip" character varying(45),
    "device_info" jsonb,
    "updated_at" timestamp with time zone NOT NULL,
    "current_portfolio_value" numeric(20,8),
    "current_room_id" uuid
);

ALTER TABLE "user_presence" ADD CONSTRAINT "user_presence_current_room_id_834311bb_fk_chat_rooms_id" FOREIGN KEY ("current_room_id") REFERENCES "chat_rooms" ("id");
ALTER TABLE "user_presence" ADD CONSTRAINT "user_presence_user_id_b93aae25_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "user_presence" ADD CONSTRAINT "user_presence_pkey" PRIMARY KEY ("user_id");

CREATE INDEX user_presence_current_room_id_834311bb ON public.user_presence USING btree (current_room_id);

-- -----------------------------------------------
-- Table: user_settings
-- -----------------------------------------------
CREATE TABLE "user_settings" (
    "id" bigint NOT NULL,
    "theme" character varying(20) NOT NULL,
    "language" character varying(10) NOT NULL,
    "timezone" character varying(64) NOT NULL,
    "receive_marketing_emails" boolean NOT NULL,
    "receive_product_updates" boolean NOT NULL,
    "extra_preferences" jsonb,
    "extended_editable_field_1" character varying(64),
    "extended_editable_field_2" character varying(64),
    "extended_editable_field_3" character varying(64),
    "extended_editable_field_4" character varying(64),
    "extended_editable_field_5" character varying(64),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "user_id" bigint NOT NULL,
    "ai_api_key_override" character varying(256),
    "ai_auto_suggestions" boolean,
    "ai_code_completion" boolean,
    "ai_context_window" integer,
    "ai_custom_instructions" text,
    "ai_default_model" character varying(64),
    "ai_max_tokens" integer,
    "ai_response_language" character varying(10),
    "ai_safety_filter" boolean,
    "ai_streaming_enabled" boolean,
    "ai_temperature" numeric(3,2),
    "ai_voice_enabled" boolean
);

ALTER TABLE "user_settings" ADD CONSTRAINT "user_settings_user_id_46a3df84_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "user_settings" ADD CONSTRAINT "user_settings_pkey" PRIMARY KEY ("id");
ALTER TABLE "user_settings" ADD CONSTRAINT "user_settings_user_id_key" UNIQUE ("user_id");

CREATE UNIQUE INDEX user_settings_user_id_key ON public.user_settings USING btree (user_id);

-- -----------------------------------------------
-- Table: users_apikey
-- -----------------------------------------------
CREATE TABLE "users_apikey" (
    "id" uuid NOT NULL,
    "environment" character varying(20) NOT NULL,
    "name" character varying(100) NOT NULL,
    "description" text NOT NULL,
    "token_hash" character varying(128) NOT NULL,
    "allowed_services" jsonb NOT NULL,
    "disallowed_services" jsonb NOT NULL,
    "scopes" jsonb NOT NULL,
    "is_read_only" boolean NOT NULL,
    "rate_limit" integer NOT NULL,
    "last_ip" character varying(45),
    "created_at" timestamp with time zone NOT NULL,
    "expires_at" timestamp with time zone,
    "is_active" boolean NOT NULL,
    "last_used_at" timestamp with time zone,
    "usage_count" integer NOT NULL,
    "allowed_ips" jsonb,
    "metadata" jsonb,
    "user_id" bigint NOT NULL
);

ALTER TABLE "users_apikey" ADD CONSTRAINT "users_apikey_user_id_330aa57f_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "users_apikey" ADD CONSTRAINT "users_apikey_pkey" PRIMARY KEY ("id");
ALTER TABLE "users_apikey" ADD CONSTRAINT "users_apikey_token_hash_key" UNIQUE ("token_hash");

CREATE INDEX users_apikey_token_hash_0f55dd18_like ON public.users_apikey USING btree (token_hash varchar_pattern_ops);
CREATE UNIQUE INDEX users_apikey_token_hash_key ON public.users_apikey USING btree (token_hash);
CREATE INDEX users_apikey_user_id_330aa57f ON public.users_apikey USING btree (user_id);

-- -----------------------------------------------
-- Table: users_corenodeprovisioner
-- -----------------------------------------------
CREATE TABLE "users_corenodeprovisioner" (
    "id" bigint NOT NULL,
    "hostname" character varying(255),
    "load_balancer" character varying(255),
    "credentials" jsonb,
    "allowed_ips" jsonb,
    "partner_cloud_hosting_details" jsonb,
    "status" character varying(50),
    "rotation_days" integer,
    "state_facts" jsonb,
    "logs_details" jsonb,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "extended_editable_field_1" character varying(64),
    "extended_editable_field_2" character varying(64),
    "extended_editable_field_3" character varying(64),
    "extended_editable_field_4" character varying(64),
    "extended_editable_field_5" character varying(64),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "ai_provisioning_success_prediction" numeric(5,2),
    "ai_error_prediction" jsonb,
    "ai_optimal_resource_allocation" jsonb,
    "ai_security_hardening_recommendations" jsonb,
    "ai_cost_efficiency_metrics" jsonb
);

ALTER TABLE "users_corenodeprovisioner" ADD CONSTRAINT "users_corenodeprovisioner_pkey" PRIMARY KEY ("id");

-- -----------------------------------------------
-- Table: users_corenodeprovisioner_insta_node_boxes
-- -----------------------------------------------
CREATE TABLE "users_corenodeprovisioner_insta_node_boxes" (
    "id" bigint NOT NULL,
    "corenodeprovisioner_id" bigint NOT NULL,
    "instanodebox_id" bigint NOT NULL
);

ALTER TABLE "users_corenodeprovisioner_insta_node_boxes" ADD CONSTRAINT "users_corenodeprovis_corenodeprovisioner__c262e370_fk_users_cor" FOREIGN KEY ("corenodeprovisioner_id") REFERENCES "users_corenodeprovisioner" ("id");
ALTER TABLE "users_corenodeprovisioner_insta_node_boxes" ADD CONSTRAINT "users_corenodeprovis_instanodebox_id_f959415a_fk_users_ins" FOREIGN KEY ("instanodebox_id") REFERENCES "users_instanodebox" ("id");
ALTER TABLE "users_corenodeprovisioner_insta_node_boxes" ADD CONSTRAINT "users_corenodeprovisioner_insta_node_boxes_pkey" PRIMARY KEY ("id");
ALTER TABLE "users_corenodeprovisioner_insta_node_boxes" ADD CONSTRAINT "users_corenodeprovisione_corenodeprovisioner_id_i_a4f1e36f_uniq" UNIQUE ("corenodeprovisioner_id", "instanodebox_id");
ALTER TABLE "users_corenodeprovisioner_insta_node_boxes" ADD CONSTRAINT "users_corenodeprovisione_corenodeprovisioner_id_i_a4f1e36f_uniq" UNIQUE ("corenodeprovisioner_id", "instanodebox_id");

CREATE UNIQUE INDEX users_corenodeprovisione_corenodeprovisioner_id_i_a4f1e36f_uniq ON public.users_corenodeprovisioner_insta_node_boxes USING btree (corenodeprovisioner_id, instanodebox_id);
CREATE INDEX users_corenodeprovisioner__corenodeprovisioner_id_c262e370 ON public.users_corenodeprovisioner_insta_node_boxes USING btree (corenodeprovisioner_id);
CREATE INDEX users_corenodeprovisioner__instanodebox_id_f959415a ON public.users_corenodeprovisioner_insta_node_boxes USING btree (instanodebox_id);

-- -----------------------------------------------
-- Table: users_instanodebox
-- -----------------------------------------------
CREATE TABLE "users_instanodebox" (
    "id" bigint NOT NULL,
    "public_ip" character varying(255),
    "private_ip" character varying(255),
    "instance_id" character varying(255),
    "public_key_ssh" text,
    "private_key_ssh" text,
    "key_pair_name" text,
    "root_username" character varying(255),
    "root_password" character varying(255),
    "hostname" character varying(255),
    "load_balancer" character varying(255),
    "custom_domain_name" character varying(255),
    "os_type" character varying(50),
    "status" character varying(50),
    "is_default_node" boolean NOT NULL,
    "box_type" character varying(100),
    "storage_gb" double precision,
    "category" character varying(100),
    "license" character varying(100),
    "custom_message" text,
    "message" text,
    "configuration" jsonb,
    "recent_activities" jsonb,
    "last_seen" timestamp with time zone NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "state_facts" jsonb,
    "state_path" character varying(255),
    "session_id" character varying(255),
    "ai_health_prediction" character varying(50),
    "ai_performance_bottlenecks" jsonb,
    "ai_scaling_recommendations" jsonb,
    "ai_security_vulnerability_score" numeric(5,2),
    "ai_maintenance_prediction" timestamp with time zone,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "user_id" bigint NOT NULL,
    "organization_id" uuid NOT NULL
);

ALTER TABLE "users_instanodebox" ADD CONSTRAINT "users_instanodebox_organization_id_4ed41c51_fk_users_org" FOREIGN KEY ("organization_id") REFERENCES "users_organization" ("id");
ALTER TABLE "users_instanodebox" ADD CONSTRAINT "users_instanodebox_user_id_e60c63bd_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "users_instanodebox" ADD CONSTRAINT "users_instanodebox_pkey" PRIMARY KEY ("id");
ALTER TABLE "users_instanodebox" ADD CONSTRAINT "users_instanodebox_hostname_key" UNIQUE ("hostname");
ALTER TABLE "users_instanodebox" ADD CONSTRAINT "users_instanodebox_public_ip_key" UNIQUE ("public_ip");

CREATE INDEX users_instanodebox_hostname_8479d62f_like ON public.users_instanodebox USING btree (hostname varchar_pattern_ops);
CREATE UNIQUE INDEX users_instanodebox_hostname_key ON public.users_instanodebox USING btree (hostname);
CREATE INDEX users_instanodebox_organization_id_4ed41c51 ON public.users_instanodebox USING btree (organization_id);
CREATE INDEX users_instanodebox_public_ip_32d5edd2_like ON public.users_instanodebox USING btree (public_ip varchar_pattern_ops);
CREATE UNIQUE INDEX users_instanodebox_public_ip_key ON public.users_instanodebox USING btree (public_ip);
CREATE INDEX users_instanodebox_user_id_e60c63bd ON public.users_instanodebox USING btree (user_id);

-- -----------------------------------------------
-- Table: users_organization
-- -----------------------------------------------
CREATE TABLE "users_organization" (
    "id" uuid NOT NULL,
    "name" character varying(255),
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "tenant_subscription_id" character varying(255),
    "tenant_primary_node_host" character varying(255),
    "tenant_primary_domain" character varying(255),
    "tenant_node_details" text,
    "tenants_users_list" jsonb,
    "tenant_alternatives_host" jsonb,
    "ai_growth_prediction" numeric(5,2),
    "ai_security_posture_score" numeric(5,2),
    "ai_resource_optimization_potential" jsonb,
    "ai_onboarding_recommendations" jsonb,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb
);

ALTER TABLE "users_organization" ADD CONSTRAINT "users_organization_pkey" PRIMARY KEY ("id");

-- -----------------------------------------------
-- Table: users_user
-- -----------------------------------------------
CREATE TABLE "users_user" (
    "id" bigint NOT NULL,
    "password" character varying(128) NOT NULL,
    "last_login" timestamp with time zone,
    "is_superuser" boolean NOT NULL,
    "username" character varying(150) NOT NULL,
    "first_name" character varying(150) NOT NULL,
    "last_name" character varying(150) NOT NULL,
    "is_staff" boolean NOT NULL,
    "is_active" boolean NOT NULL,
    "date_joined" timestamp with time zone NOT NULL,
    "deployed_where" character varying(16),
    "email" character varying(254),
    "phone" character varying(15),
    "company_name" character varying(255),
    "mfa_enabled" boolean NOT NULL,
    "mfa_secret" character varying(32),
    "mfa_backup_codes" jsonb,
    "mfa_last_used" timestamp with time zone,
    "mfa_setup_completed" boolean NOT NULL,
    "mfa_device_name" character varying(100),
    "mfa_last_verified" timestamp with time zone,
    "last_otp_secret" character varying(32) NOT NULL,
    "verification_code" character varying(100),
    "coupon_code" character varying(100),
    "is_verified" boolean NOT NULL,
    "kyc_completed" boolean NOT NULL,
    "kyc_verified_date" timestamp with time zone,
    "kyc_rejected_reason" text,
    "last_kyc_update" timestamp with time zone NOT NULL,
    "profile_avatar" character varying(250),
    "nationality" character varying(250),
    "gender" character varying(250),
    "id_type" character varying(250),
    "id_number" character varying(100),
    "id_issuing_country" character varying(100),
    "id_issue_date" date,
    "id_expiry_date" date,
    "id_document_front" character varying(100),
    "id_document_back" character varying(100),
    "place_of_birth" character varying(255),
    "tax_identification_number" character varying(100),
    "occupation" character varying(255),
    "purpose_of_account" text,
    "address_line1" character varying(255),
    "address_line2" character varying(255),
    "city" character varying(100),
    "state_province" character varying(100),
    "postal_code" character varying(50),
    "country" character varying(100),
    "address_proof_document" character varying(100),
    "source_of_funds" character varying(255),
    "estimated_annual_income" numeric(12,2),
    "is_restricted" boolean NOT NULL,
    "social_google" character varying(255),
    "social_microsoft" character varying(255),
    "social_github" character varying(255),
    "custom_notification" text,
    "query_terms" jsonb,
    "inputs" jsonb,
    "search_keys" jsonb,
    "search_results" jsonb,
    "ai_risk_score" numeric(5,2),
    "ai_sentiment_analysis" jsonb,
    "ai_recommended_actions" jsonb,
    "ai_activity_anomaly_detected" boolean NOT NULL,
    "user_feedback_on_ai" jsonb,
    "ai_model_editable_field_1" character varying,
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying,
    "ai_model_editable_field_6" character varying,
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "organization_id" uuid
);

ALTER TABLE "users_user" ADD CONSTRAINT "users_user_organization_id_70643736_fk_users_organization_id" FOREIGN KEY ("organization_id") REFERENCES "users_organization" ("id");
ALTER TABLE "users_user" ADD CONSTRAINT "users_user_pkey" PRIMARY KEY ("id");
ALTER TABLE "users_user" ADD CONSTRAINT "users_user_email_key" UNIQUE ("email");
ALTER TABLE "users_user" ADD CONSTRAINT "users_user_phone_key" UNIQUE ("phone");
ALTER TABLE "users_user" ADD CONSTRAINT "users_user_username_key" UNIQUE ("username");

CREATE INDEX users_user_email_243f6e77_like ON public.users_user USING btree (email varchar_pattern_ops);
CREATE UNIQUE INDEX users_user_email_key ON public.users_user USING btree (email);
CREATE INDEX users_user_organization_id_70643736 ON public.users_user USING btree (organization_id);
CREATE INDEX users_user_phone_fe37f55c_like ON public.users_user USING btree (phone varchar_pattern_ops);
CREATE UNIQUE INDEX users_user_phone_key ON public.users_user USING btree (phone);
CREATE INDEX users_user_username_06e46fe6_like ON public.users_user USING btree (username varchar_pattern_ops);
CREATE UNIQUE INDEX users_user_username_key ON public.users_user USING btree (username);

-- -----------------------------------------------
-- Table: users_user_groups
-- -----------------------------------------------
CREATE TABLE "users_user_groups" (
    "id" bigint NOT NULL,
    "user_id" bigint NOT NULL,
    "group_id" integer NOT NULL
);

ALTER TABLE "users_user_groups" ADD CONSTRAINT "users_user_groups_group_id_9afc8d0e_fk_auth_group_id" FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id");
ALTER TABLE "users_user_groups" ADD CONSTRAINT "users_user_groups_user_id_5f6f5a90_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "users_user_groups" ADD CONSTRAINT "users_user_groups_pkey" PRIMARY KEY ("id");
ALTER TABLE "users_user_groups" ADD CONSTRAINT "users_user_groups_user_id_group_id_b88eab82_uniq" UNIQUE ("user_id", "group_id");
ALTER TABLE "users_user_groups" ADD CONSTRAINT "users_user_groups_user_id_group_id_b88eab82_uniq" UNIQUE ("user_id", "group_id");

CREATE INDEX users_user_groups_group_id_9afc8d0e ON public.users_user_groups USING btree (group_id);
CREATE INDEX users_user_groups_user_id_5f6f5a90 ON public.users_user_groups USING btree (user_id);
CREATE UNIQUE INDEX users_user_groups_user_id_group_id_b88eab82_uniq ON public.users_user_groups USING btree (user_id, group_id);

-- -----------------------------------------------
-- Table: users_user_user_permissions
-- -----------------------------------------------
CREATE TABLE "users_user_user_permissions" (
    "id" bigint NOT NULL,
    "user_id" bigint NOT NULL,
    "permission_id" integer NOT NULL
);

ALTER TABLE "users_user_user_permissions" ADD CONSTRAINT "users_user_user_perm_permission_id_0b93982e_fk_auth_perm" FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id");
ALTER TABLE "users_user_user_permissions" ADD CONSTRAINT "users_user_user_permissions_user_id_20aca447_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");
ALTER TABLE "users_user_user_permissions" ADD CONSTRAINT "users_user_user_permissions_pkey" PRIMARY KEY ("id");
ALTER TABLE "users_user_user_permissions" ADD CONSTRAINT "users_user_user_permissions_user_id_permission_id_43338c45_uniq" UNIQUE ("user_id", "permission_id");
ALTER TABLE "users_user_user_permissions" ADD CONSTRAINT "users_user_user_permissions_user_id_permission_id_43338c45_uniq" UNIQUE ("user_id", "permission_id");

CREATE INDEX users_user_user_permissions_permission_id_0b93982e ON public.users_user_user_permissions USING btree (permission_id);
CREATE INDEX users_user_user_permissions_user_id_20aca447 ON public.users_user_user_permissions USING btree (user_id);
CREATE UNIQUE INDEX users_user_user_permissions_user_id_permission_id_43338c45_uniq ON public.users_user_user_permissions USING btree (user_id, permission_id);

-- -----------------------------------------------
-- Table: vibe_coding_sessions
-- -----------------------------------------------
CREATE TABLE "vibe_coding_sessions" (
    "id" uuid NOT NULL,
    "agent_session_id" uuid,
    "studio_project_id" uuid,
    "active_file_path" character varying(512),
    "project_context" jsonb NOT NULL,
    "last_code_edit" timestamp with time zone,
    "vibe_mode" character varying(50),
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "ai_model_editable_field_1" character varying(255),
    "ai_model_editable_field_2" jsonb,
    "ai_model_editable_field_3" jsonb,
    "ai_model_editable_field_4" jsonb,
    "ai_model_editable_field_5" character varying(255),
    "ai_model_editable_field_6" character varying(255),
    "extended_editable_field_1" character varying(255),
    "extended_editable_field_2" character varying(255),
    "extended_editable_field_3" character varying(255),
    "extended_editable_field_4" character varying(255),
    "extended_editable_field_5" character varying(255),
    "extended_boolean_field_1" boolean,
    "extended_boolean_field_2" boolean,
    "extended_boolean_field_3" boolean,
    "extended_boolean_field_4" boolean,
    "extended_boolean_field_5" boolean,
    "extended_json_field_1" jsonb,
    "extended_json_field_2" jsonb,
    "extended_json_field_3" jsonb,
    "extended_json_field_4" jsonb,
    "extended_json_field_5" jsonb,
    "extended_json_field_6" jsonb,
    "extended_json_field_7" jsonb,
    "extended_json_field_8" jsonb,
    "extended_json_field_9" jsonb,
    "extended_json_field_10" jsonb
);

ALTER TABLE "vibe_coding_sessions" ADD CONSTRAINT "vibe_coding_sessions_pkey" PRIMARY KEY ("id");

CREATE INDEX vibe_coding_agent_s_56879a_idx ON public.vibe_coding_sessions USING btree (agent_session_id);
CREATE INDEX vibe_coding_sessions_agent_session_id_e9cfce30 ON public.vibe_coding_sessions USING btree (agent_session_id);
CREATE INDEX vibe_coding_sessions_studio_project_id_01c1712c ON public.vibe_coding_sessions USING btree (studio_project_id);
CREATE INDEX vibe_coding_studio__af2f79_idx ON public.vibe_coding_sessions USING btree (studio_project_id);

-- -----------------------------------------------
-- Table: webhooks
-- -----------------------------------------------
CREATE TABLE "webhooks" (
    "id" uuid NOT NULL,
    "webhook_url" character varying(500) NOT NULL,
    "webhook_secret" character varying(255) NOT NULL,
    "events" jsonb NOT NULL,
    "branch_filter" jsonb NOT NULL,
    "is_active" boolean NOT NULL,
    "last_triggered" timestamp with time zone,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL,
    "pipeline_id" uuid NOT NULL,
    "repository_id" uuid
);

ALTER TABLE "webhooks" ADD CONSTRAINT "webhooks_pipeline_id_25b661c4_fk_pipelines_id" FOREIGN KEY ("pipeline_id") REFERENCES "pipelines" ("id");
ALTER TABLE "webhooks" ADD CONSTRAINT "webhooks_repository_id_a9ff97ff_fk_git_repositories_id" FOREIGN KEY ("repository_id") REFERENCES "git_repositories" ("id");
ALTER TABLE "webhooks" ADD CONSTRAINT "webhooks_pkey" PRIMARY KEY ("id");

CREATE INDEX webhooks_created_at_5f1e9cff ON public.webhooks USING btree (created_at);
CREATE INDEX webhooks_pipelin_c9e6ed_idx ON public.webhooks USING btree (pipeline_id, is_active);
CREATE INDEX webhooks_pipeline_id_25b661c4 ON public.webhooks USING btree (pipeline_id);
CREATE INDEX webhooks_reposit_4ba39a_idx ON public.webhooks USING btree (repository_id);
CREATE INDEX webhooks_repository_id_a9ff97ff ON public.webhooks USING btree (repository_id);


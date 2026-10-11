"""0001 initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('settings_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 2. Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='Lead Architect'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 3. Jobs
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('queue', sa.String(length=50), nullable=False, server_default='default'),
        sa.Column('task_name', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('attempts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_jobs_queue'), 'jobs', ['queue'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    op.create_index(op.f('ix_jobs_task_name'), 'jobs', ['task_name'], unique=False)

    # 4. Projects
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, server_default='v1.0'),
        sa.Column('domain', sa.String(100), nullable=False, server_default='General'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='analyzed'),
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('open_ambiguities_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parsed_requirements_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lint_mode', sa.String(50), nullable=False, server_default='Strict INCOSE'),
        sa.Column('retention_mode', sa.String(50), nullable=False, server_default='standard'),
        sa.Column('document_filename', sa.String(255), nullable=True),
        sa.Column('document_size_bytes', sa.Integer(), nullable=True),
        sa.Column('document_sha256', sa.String(64), nullable=True),
        sa.Column('last_analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 5. Requirements
    op.create_table(
        'requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('req_id_str', sa.String(50), nullable=False),
        sa.Column('type', sa.String(50), nullable=False, server_default='Functional'),
        sa.Column('category', sa.String(100), nullable=False, server_default='General'),
        sa.Column('clause_text', sa.Text(), nullable=False),
        sa.Column('clarity_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='verified'),
        sa.Column('rule_violations', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('score_boost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 6. Issues
    op.create_table(
        'issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('issue_id_str', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False, server_default='High'),
        sa.Column('category', sa.String(100), nullable=False, server_default='Contradiction'),
        sa.Column('affected_req_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('evidence_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 7. Analysis Runs
    op.create_table(
        'analysis_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_filename', sa.String(255), nullable=False),
        sa.Column('document_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('document_sha256', sa.String(64), nullable=False, server_default=''),
        sa.Column('context_standard', sa.String(100), nullable=False, server_default='ISO/IEC/IEEE 29148'),
        sa.Column('analysis_mode', sa.String(50), nullable=False, server_default='Deep Semantics v2.4'),
        sa.Column('status', sa.String(50), nullable=False, server_default='in_progress'),
        sa.Column('current_stage', sa.String(100), nullable=False, server_default='Stage 1 of 6'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_requirements', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_requirements', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('throughput_req_per_sec', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('elapsed_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('eta_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('logs', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 8. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('details_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('analysis_runs')
    op.drop_table('issues')
    op.drop_table('requirements')
    op.drop_table('projects')
    op.drop_table('jobs')
    op.drop_table('users')
    op.drop_table('organizations')

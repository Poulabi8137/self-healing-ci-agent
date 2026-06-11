"""phase1_initial_schema

Revision ID: 8c797aafde43
Revises: 5c1fd0ccce04
Create Date: 2026-06-11 02:27:44.717661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8c797aafde43'
down_revision: Union[str, Sequence[str], None] = '5c1fd0ccce04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New tables
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('google_id', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id')
    )
    op.create_table('webhook_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('github_installation_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=True),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('github_installations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('installation_id', sa.Integer(), nullable=False),
        sa.Column('account_login', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.String(length=50), nullable=True),
        sa.Column('account_avatar', sa.String(length=500), nullable=True),
        sa.Column('repos_selected', sa.Text(), nullable=True),
        sa.Column('access_token', sa.String(length=500), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('installation_id')
    )
    op.create_table('investigations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('failure_id', sa.Integer(), nullable=True),
        sa.Column('repository_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('error_category', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('stages', sa.Text(), nullable=True),
        sa.Column('current_stage', sa.String(length=100), nullable=True),
        sa.Column('current_stage_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['failure_id'], ['failures.id'], ),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Batch mode for SQLite ALTER TABLE support on existing tables
    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_api_keys_user_id', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('failures') as batch_op:
        batch_op.add_column(sa.Column('github_installation_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('investigation_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('repositories') as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('last_workflow_status', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('last_workflow_run_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('failure_count', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('repositories') as batch_op:
        batch_op.drop_column('failure_count')
        batch_op.drop_column('last_workflow_run_at')
        batch_op.drop_column('last_workflow_status')
        batch_op.drop_column('is_active')

    with op.batch_alter_table('failures') as batch_op:
        batch_op.drop_column('investigation_id')
        batch_op.drop_column('github_installation_id')

    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.drop_constraint('fk_api_keys_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')

    op.drop_table('investigations')
    op.drop_table('github_installations')
    op.drop_table('audit_logs')
    op.drop_table('webhook_events')
    op.drop_table('users')

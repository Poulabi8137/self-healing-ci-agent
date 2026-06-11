"""phase3_github_linking

Revision ID: 93f898fdef21
Revises: 20ab121f8098
Create Date: 2026-06-11 09:48:17.237182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '93f898fdef21'
down_revision: Union[str, Sequence[str], None] = '20ab121f8098'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New table — safe for SQLite
    op.create_table('investigation_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('investigation_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add/remove columns with batch mode for SQLite compatibility
    with op.batch_alter_table('github_installations') as batch_op:
        batch_op.add_column(sa.Column('account_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('github_id', sa.Integer(), nullable=True))
        batch_op.drop_column('access_token')

    with op.batch_alter_table('repositories') as batch_op:
        batch_op.add_column(sa.Column('github_installation_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_repositories_github_installation_id',
            'github_installations',
            ['github_installation_id'],
            ['id'],
        )

    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('github_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('github_username', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('github_email', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('uq_users_github_id', ['github_id'])

    with op.batch_alter_table('webhook_events') as batch_op:
        batch_op.add_column(sa.Column('delivery_id', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('uq_webhook_events_delivery_id', ['delivery_id'])


def downgrade() -> None:
    with op.batch_alter_table('webhook_events') as batch_op:
        batch_op.drop_constraint('uq_webhook_events_delivery_id', type_='unique')
        batch_op.drop_column('delivery_id')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_constraint('uq_users_github_id', type_='unique')
        batch_op.drop_column('github_email')
        batch_op.drop_column('github_username')
        batch_op.drop_column('github_id')

    with op.batch_alter_table('repositories') as batch_op:
        batch_op.drop_constraint('fk_repositories_github_installation_id', type_='foreignkey')
        batch_op.drop_column('github_installation_id')

    with op.batch_alter_table('github_installations') as batch_op:
        batch_op.add_column(sa.Column('access_token', sa.String(length=500), nullable=True))
        batch_op.drop_column('github_id')
        batch_op.drop_column('account_url')

    op.drop_table('investigation_events')

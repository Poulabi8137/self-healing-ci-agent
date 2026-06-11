"""phase1_missing_columns

Revision ID: 20ab121f8098
Revises: 8c797aafde43
Create Date: 2026-06-11 02:29:36.155531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20ab121f8098'
down_revision: Union[str, Sequence[str], None] = '8c797aafde43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('api_keys') as batch_op:
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

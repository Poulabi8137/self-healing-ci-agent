"""extend pr_records with investigation_id, pr_number, pr_url, description

Revision ID: 3d4e5f6a7b8c
Revises: 2c3d4e5f6a7b
Create Date: 2026-06-11 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3d4e5f6a7b8c'
down_revision: Union[str, Sequence[str], None] = '2c3d4e5f6a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('pr_records') as batch_op:
        batch_op.add_column(sa.Column('investigation_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('repository_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('pr_number', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('pr_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.create_foreign_key('fk_pr_records_investigation_id', 'investigations', ['investigation_id'], ['id'])
        batch_op.create_foreign_key('fk_pr_records_repository_id', 'repositories', ['repository_id'], ['id'])
        batch_op.create_index('idx_pr_investigation', ['investigation_id'])


def downgrade() -> None:
    with op.batch_alter_table('pr_records') as batch_op:
        batch_op.drop_index('idx_pr_investigation')
        batch_op.drop_constraint('fk_pr_records_repository_id', type_='foreignkey')
        batch_op.drop_constraint('fk_pr_records_investigation_id', type_='foreignkey')
        batch_op.drop_column('description')
        batch_op.drop_column('pr_url')
        batch_op.drop_column('pr_number')
        batch_op.drop_column('repository_id')
        batch_op.drop_column('investigation_id')

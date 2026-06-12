"""add fix_artifacts table

Revision ID: 2c3d4e5f6a7b
Revises: 1b2c3d4e5f6a
Create Date: 2026-06-11 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2c3d4e5f6a7b'
down_revision: Union[str, Sequence[str], None] = '1b2c3d4e5f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('fix_artifacts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('investigation_id', sa.Integer(), nullable=False),
        sa.Column('fix_summary', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('files_modified', sa.Text(), nullable=True),
        sa.Column('patch_content', sa.Text(), nullable=True),
        sa.Column('branch_name', sa.String(length=255), nullable=True),
        sa.Column('dry_run', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='generated'),
        sa.Column('generated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('fix_artifacts')

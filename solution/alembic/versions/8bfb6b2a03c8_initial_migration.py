"""Initial migration

Revision ID: 8bfb6b2a03c8
Revises: dcf620a74ea9
Create Date: 2025-02-20 18:01:03.735581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bfb6b2a03c8'
down_revision: Union[str, None] = 'dcf620a74ea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('campaigns', 'cost_per_impression',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=False)
    op.alter_column('campaigns', 'cost_per_click',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('campaigns', 'cost_per_click',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
    op.alter_column('campaigns', 'cost_per_impression',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
    # ### end Alembic commands ###

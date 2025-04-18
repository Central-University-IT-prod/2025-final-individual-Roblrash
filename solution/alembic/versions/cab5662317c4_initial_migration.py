"""Initial migration

Revision ID: cab5662317c4
Revises: 6fd8ae09b12c
Create Date: 2025-02-20 19:17:43.320688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cab5662317c4'
down_revision: Union[str, None] = '6fd8ae09b12c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('campaigns', 'cost_per_impression',
               existing_type=sa.INTEGER(),
               type_=sa.Numeric(),
               existing_nullable=False)
    op.alter_column('campaigns', 'cost_per_click',
               existing_type=sa.INTEGER(),
               type_=sa.Numeric(),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('campaigns', 'cost_per_click',
               existing_type=sa.Numeric(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('campaigns', 'cost_per_impression',
               existing_type=sa.Numeric(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    # ### end Alembic commands ###

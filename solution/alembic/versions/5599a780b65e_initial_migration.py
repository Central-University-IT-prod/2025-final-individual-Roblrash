"""Initial migration

Revision ID: 5599a780b65e
Revises: 8290cd14c054
Create Date: 2025-02-12 13:56:36.268221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5599a780b65e'
down_revision: Union[str, None] = '8290cd14c054'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Обновляем таблицу advertisers:
    # 1. Сначала удаляем внешний ключ в таблице ml_scores, который ссылается на advertisers.id.
    op.drop_constraint('ml_scores_advertiser_id_fkey', 'ml_scores', type_='foreignkey')
    # 2. Переименовываем столбец id в таблице advertisers в advertiser_id.
    op.execute("ALTER TABLE advertisers RENAME COLUMN id TO advertiser_id")
    # 3. Удаляем старый индекс и создаем новый на переименованном столбце.
    op.drop_index('ix_advertisers_id', table_name='advertisers')
    op.create_index(op.f('ix_advertisers_advertiser_id'), 'advertisers', ['advertiser_id'], unique=False)
    # 4. Создаем новый внешний ключ в таблице ml_scores, ссылающийся на advertisers.advertiser_id.
    op.create_foreign_key(None, 'ml_scores', 'advertisers', ['advertiser_id'], ['advertiser_id'])

    # Обновляем таблицу users аналогичным образом:
    op.drop_constraint('ml_scores_client_id_fkey', 'ml_scores', type_='foreignkey')
    op.execute("ALTER TABLE users RENAME COLUMN id TO client_id")
    op.drop_index('ix_users_id', table_name='users')
    op.create_index(op.f('ix_users_client_id'), 'users', ['client_id'], unique=False)
    op.create_foreign_key(None, 'ml_scores', 'users', ['client_id'], ['client_id'])


def downgrade() -> None:
    # Откат для таблицы ml_scores:
    op.drop_constraint(None, 'ml_scores', type_='foreignkey')
    # Восстанавливаем внешний ключ для advertisers (ссылается на столбец advertisers.id, который будет восстановлен ниже)
    op.create_foreign_key('ml_scores_advertiser_id_fkey', 'ml_scores', 'advertisers', ['advertiser_id'], ['id'])
    # Восстанавливаем внешний ключ для users
    op.create_foreign_key('ml_scores_client_id_fkey', 'ml_scores', 'users', ['client_id'], ['id'])

    # Откат для таблицы users:
    op.drop_index(op.f('ix_users_client_id'), table_name='users')
    op.execute("ALTER TABLE users RENAME COLUMN client_id TO id")
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Откат для таблицы advertisers:
    op.drop_index(op.f('ix_advertisers_advertiser_id'), table_name='advertisers')
    op.execute("ALTER TABLE advertisers RENAME COLUMN advertiser_id TO id")
    op.create_index('ix_advertisers_id', 'advertisers', ['id'], unique=False)

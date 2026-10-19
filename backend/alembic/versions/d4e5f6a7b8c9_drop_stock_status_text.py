"""drop stock_status_text column from crawl_results

Revision ID: d4e5f6a7b8c9
Revises: c1a9f3b8e721
Create Date: 2026-10-19 13:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c1a9f3b8e721'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [col['name'] for col in insp.get_columns('crawl_results')]

    if 'stock_status_text' in cols:
        with op.batch_alter_table('crawl_results', schema=None) as batch_op:
            batch_op.drop_column('stock_status_text')


def downgrade() -> None:
    with op.batch_alter_table('crawl_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock_status_text', sa.String(length=100), nullable=True))

"""drop pricing_audit_logs entity_id foreign key constraint

Revision ID: c1a9f3b8e721
Revises: dbbe0db0b38f
Create Date: 2026-10-19 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a9f3b8e721'
down_revision: Union[str, None] = 'dbbe0db0b38f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PricingAuditLog is a polymorphic log for price_recommendations, sku_mappings, etc.
    # Therefore entity_id should not have a rigid foreign key constraint to price_recommendations.
    bind = op.get_bind()
    insp = sa.inspect(bind)
    fks = insp.get_foreign_keys('pricing_audit_logs')
    fk_names = [fk['name'] for fk in fks if fk.get('name')]

    if 'pricing_audit_logs_entity_id_fkey' in fk_names:
        with op.batch_alter_table('pricing_audit_logs', schema=None) as batch_op:
            batch_op.drop_constraint('pricing_audit_logs_entity_id_fkey', type_='foreignkey')


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    fks = insp.get_foreign_keys('pricing_audit_logs')
    fk_names = [fk['name'] for fk in fks if fk.get('name')]

    if 'pricing_audit_logs_entity_id_fkey' not in fk_names:
        with op.batch_alter_table('pricing_audit_logs', schema=None) as batch_op:
            batch_op.create_foreign_key(
                'pricing_audit_logs_entity_id_fkey',
                'price_recommendations',
                ['entity_id'],
                ['id']
            )

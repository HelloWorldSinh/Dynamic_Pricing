"""expand_comprehensive_schema

Revision ID: dbbe0db0b38f
Revises: f6895e80f54d
Create Date: 2026-10-05 13:29:16.567666

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import app.models.base

# revision identifiers, used by Alembic.
revision: str = 'dbbe0db0b38f'
down_revision: Union[str, Sequence[str], None] = 'f6895e80f54d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Nâng cấp schema từ 4 bảng ban đầu lên đầy đủ 14 bảng toàn hệ thống."""
    # 1. Bổ sung bảng crawl_jobs trước để crawl_results có thể tham chiếu FK
    op.create_table(
        'crawl_jobs',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('trigger_type', sa.String(length=30), nullable=False, server_default='SCHEDULED'),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='ALL'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='ALL'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('crawl_jobs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_crawl_jobs_status'), ['status'], unique=False)

    # 2. Cập nhật bảng products với các trường giá và biên lợi nhuận
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost_price', sa.BigInteger(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('min_margin_pct', sa.Float(), nullable=False, server_default='5.0'))
        batch_op.add_column(sa.Column('floor_price', sa.BigInteger(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('base_retail_price', sa.BigInteger(), nullable=False, server_default='0'))

    # 3. Cập nhật bảng crawl_results với job_id và stock_status_text
    with op.batch_alter_table('crawl_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('job_id', app.models.base.GUID(), nullable=True))
        batch_op.add_column(sa.Column('stock_status_text', sa.String(length=100), nullable=True))
        batch_op.create_index(batch_op.f('ix_crawl_results_job_id'), ['job_id'], unique=False)
        batch_op.create_foreign_key('fk_crawl_results_job_id', 'crawl_jobs', ['job_id'], ['id'])

    # 4. Cập nhật bảng sku_mappings với trường duyệt kiểm toán
    with op.batch_alter_table('sku_mappings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reviewed_by', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_sku_mappings_status'), ['status'], unique=False)

    # 5. Phân hệ Tồn kho đa kho (Warehouses & Inventory Snapshots)
    op.create_table(
        'warehouses',
        sa.Column('warehouse_id', sa.String(length=50), nullable=False),
        sa.Column('warehouse_name', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('warehouse_id')
    )

    op.create_table(
        'inventory_snapshots',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('fpt_product_id', app.models.base.GUID(), nullable=False),
        sa.Column('warehouse_id', sa.String(length=50), nullable=False),
        sa.Column('snapshot_ts', sa.DateTime(), nullable=False),
        sa.Column('qty_on_hand', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('qty_reserved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('qty_available', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('target_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('safety_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stock_cover_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_obsolescence_risk', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('holding_cost_pct_monthly', sa.Float(), nullable=False, server_default='1.5'),
        sa.Column('competitor_oos_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['fpt_product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.warehouse_id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_snapshots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_inventory_snapshots_fpt_product_id'), ['fpt_product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_inventory_snapshots_warehouse_id'), ['warehouse_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_inventory_snapshots_snapshot_ts'), ['snapshot_ts'], unique=False)
        batch_op.create_index(batch_op.f('ix_inventory_snapshots_is_obsolescence_risk'), ['is_obsolescence_risk'], unique=False)

    # 6. Phân hệ Nhu cầu (Demand Events & Demand Hourly Aggregates)
    op.create_table(
        'demand_events',
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('fpt_product_id', app.models.base.GUID(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_ts', sa.DateTime(), nullable=False),
        sa.Column('time_on_page_sec', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scroll_depth_pct', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_repeat_view', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_bounce', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('cart_action', sa.String(length=50), nullable=True),
        sa.Column('search_keyword', sa.String(length=255), nullable=True),
        sa.Column('exit_url_domain', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['fpt_product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('event_id')
    )
    with op.batch_alter_table('demand_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_demand_events_fpt_product_id'), ['fpt_product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_demand_events_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_demand_events_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_demand_events_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_demand_events_event_ts'), ['event_ts'], unique=False)

    op.create_table(
        'demand_hourly_aggregates',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('fpt_product_id', app.models.base.GUID(), nullable=False),
        sa.Column('aggregate_hour', sa.DateTime(), nullable=False),
        sa.Column('total_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('search_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cart_adds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('purchases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cvr_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('demand_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['fpt_product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('demand_hourly_aggregates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_demand_hourly_aggregates_fpt_product_id'), ['fpt_product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_demand_hourly_aggregates_aggregate_hour'), ['aggregate_hour'], unique=False)

    # 7. Phân hệ Định giá Động (Price Recommendations, History & Audit Logs)
    op.create_table(
        'price_recommendations',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('fpt_product_id', app.models.base.GUID(), nullable=False),
        sa.Column('current_fpt_price', sa.BigInteger(), nullable=False),
        sa.Column('competitor_min_price', sa.BigInteger(), nullable=True),
        sa.Column('recommended_price', sa.BigInteger(), nullable=False),
        sa.Column('price_delta_amount', sa.BigInteger(), nullable=False),
        sa.Column('price_delta_pct', sa.Float(), nullable=False),
        sa.Column('demand_score', sa.Float(), nullable=False),
        sa.Column('inventory_score', sa.Float(), nullable=False),
        sa.Column('competitor_score', sa.Float(), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=False),
        sa.Column('scenario_name', sa.String(length=100), nullable=False),
        sa.Column('reasoning_3layers', sa.JSON(), nullable=False),
        sa.Column('is_floor_capped', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('reviewed_by', sa.String(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['fpt_product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('price_recommendations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_price_recommendations_fpt_product_id'), ['fpt_product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_price_recommendations_composite_score'), ['composite_score'], unique=False)
        batch_op.create_index(batch_op.f('ix_price_recommendations_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_price_recommendations_created_at'), ['created_at'], unique=False)

    op.create_table(
        'price_history',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('fpt_product_id', app.models.base.GUID(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('price', sa.BigInteger(), nullable=False),
        sa.Column('is_in_stock', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['fpt_product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('price_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_price_history_fpt_product_id'), ['fpt_product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_price_history_source'), ['source'], unique=False)
        batch_op.create_index(batch_op.f('ix_price_history_recorded_at'), ['recorded_at'], unique=False)

    op.create_table(
        'pricing_audit_logs',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', app.models.base.GUID(), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['entity_id'], ['price_recommendations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Phân hệ Trợ lý AI (Chat Sessions & Messages)
    op.create_table(
        'chat_sessions',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='Cuộc hội thoại mới'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('chat_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_chat_sessions_user_id'), ['user_id'], unique=False)

    op.create_table(
        'chat_messages',
        sa.Column('id', app.models.base.GUID(), nullable=False),
        sa.Column('session_id', app.models.base.GUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('retrieved_context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_chat_messages_session_id'), ['session_id'], unique=False)


def downgrade() -> None:
    """Hạ cấp rollback toàn bộ các bảng và cột đã thêm."""
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('pricing_audit_logs')
    op.drop_table('price_history')
    op.drop_table('price_recommendations')
    op.drop_table('demand_hourly_aggregates')
    op.drop_table('demand_events')
    op.drop_table('inventory_snapshots')
    op.drop_table('warehouses')

    with op.batch_alter_table('sku_mappings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sku_mappings_status'))
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('reviewed_by')

    with op.batch_alter_table('crawl_results', schema=None) as batch_op:
        batch_op.drop_constraint('fk_crawl_results_job_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_crawl_results_job_id'))
        batch_op.drop_column('stock_status_text')
        batch_op.drop_column('job_id')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('base_retail_price')
        batch_op.drop_column('floor_price')
        batch_op.drop_column('min_margin_pct')
        batch_op.drop_column('cost_price')

    op.drop_table('crawl_jobs')

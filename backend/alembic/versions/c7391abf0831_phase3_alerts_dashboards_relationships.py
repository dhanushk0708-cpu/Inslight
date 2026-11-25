"""phase3_alerts_dashboards_relationships

Revision ID: c7391abf0831
Revises: b4280f8d0630
Create Date: 2026-11-24 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7391abf0831'
down_revision: Union[str, Sequence[str], None] = 'b4280f8d0630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with Phase 3 tables."""
    # 1. Alerts Table
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_json', sa.Text(), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=True),
        sa.Column('observed_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)
    op.create_index(op.f('ix_alerts_dataset_id'), 'alerts', ['dataset_id'], unique=False)

    # 2. Alert Rules Table
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('condition', sa.String(length=30), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True, server_default='business_rule'),
        sa.Column('severity', sa.String(length=20), nullable=True, server_default='high'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_rules_user_id'), 'alert_rules', ['user_id'], unique=False)
    op.create_index(op.f('ix_alert_rules_dataset_id'), 'alert_rules', ['dataset_id'], unique=False)

    # 3. Saved Dashboards Table
    op.create_table(
        'saved_dashboards',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('layout_config', sa.Text(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_dashboards_user_id'), 'saved_dashboards', ['user_id'], unique=False)
    op.create_index(op.f('ix_saved_dashboards_dataset_id'), 'saved_dashboards', ['dataset_id'], unique=False)

    # 4. Dataset Relationships Table
    op.create_table(
        'dataset_relationships',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('source_dataset_id', sa.String(length=36), nullable=False),
        sa.Column('target_dataset_id', sa.String(length=36), nullable=False),
        sa.Column('source_column', sa.String(length=100), nullable=False),
        sa.Column('target_column', sa.String(length=100), nullable=False),
        sa.Column('relationship_type', sa.String(length=30), nullable=False, server_default='many_to_one'),
        sa.Column('cardinality_status', sa.String(length=50), nullable=False, server_default='verified'),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_relationships_user_id'), 'dataset_relationships', ['user_id'], unique=False)
    op.create_index(op.f('ix_dataset_relationships_source_id'), 'dataset_relationships', ['source_dataset_id'], unique=False)
    op.create_index(op.f('ix_dataset_relationships_target_id'), 'dataset_relationships', ['target_dataset_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('dataset_relationships')
    op.drop_table('saved_dashboards')
    op.drop_table('alert_rules')
    op.drop_table('alerts')

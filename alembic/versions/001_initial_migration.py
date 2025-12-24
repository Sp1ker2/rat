"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-23 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('token', sa.String(64), nullable=False, unique=True),
        sa.Column('imei', sa.String(32), nullable=True),
        sa.Column('model', sa.String(255), nullable=True),
        sa.Column('manufacturer', sa.String(255), nullable=True),
        sa.Column('android_version', sa.String(50), nullable=True),
        sa.Column('sdk', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index('ix_devices_token', 'devices', ['token'])
    
    # Create camera_frames table
    op.create_table(
        'camera_frames',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('camera', sa.String(10), nullable=False),
        sa.Column('frame_data', postgresql.BYTEA(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_camera_frames_device_id', 'camera_frames', ['device_id'])
    op.create_index('ix_camera_frames_timestamp', 'camera_frames', ['timestamp'])
    op.create_index('ix_camera_frames_created_at', 'camera_frames', ['created_at'])
    
    # Create location_history table
    op.create_table(
        'location_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_location_history_device_id', 'location_history', ['device_id'])
    op.create_index('ix_location_history_timestamp', 'location_history', ['timestamp'])
    op.create_index('ix_location_history_created_at', 'location_history', ['created_at'])
    
    # Create device_events table
    op.create_table(
        'device_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_device_events_device_id', 'device_events', ['device_id'])
    op.create_index('ix_device_events_event_type', 'device_events', ['event_type'])
    op.create_index('ix_device_events_timestamp', 'device_events', ['timestamp'])
    op.create_index('ix_device_events_created_at', 'device_events', ['created_at'])


def downgrade() -> None:
    op.drop_table('device_events')
    op.drop_table('location_history')
    op.drop_table('camera_frames')
    op.drop_table('devices')



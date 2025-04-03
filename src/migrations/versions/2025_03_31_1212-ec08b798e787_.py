"""empty message

Revision ID: ec08b798e787
Revises: 
Create Date: 2025-03-31 12:12:18.560375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec08b798e787'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=256), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_updated_at'), 'users', ['updated_at'], unique=False)
    op.create_table('generations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('external_file_id', sa.String(length=256), nullable=False),
    sa.Column('external_task_id', sa.String(length=256), nullable=False),
    sa.Column('storage_url', sa.String(length=256), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('QUEUEING', 'PREPARING', 'PROCESSING', 'SUCCESS', 'FAIL', name='querystatusenums'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('external_file_id'),
    sa.UniqueConstraint('external_task_id'),
    sa.UniqueConstraint('storage_url')
    )
    op.create_index(op.f('ix_generations_updated_at'), 'generations', ['updated_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_generations_updated_at'), table_name='generations')
    op.drop_table('generations')
    op.drop_index(op.f('ix_users_updated_at'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###

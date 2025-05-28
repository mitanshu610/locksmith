"""add membership id

Revision ID: 8eab41baa873
Revises: 537fe42cab74
Create Date: 2025-05-05 15:42:26.502610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '8eab41baa873'
down_revision: Union[str, None] = '537fe42cab74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the membership_id column first, but allow NULL temporarily
    op.add_column('team_memberships', sa.Column('membership_id', UUID(as_uuid=True), nullable=True))

    # Generate UUID values for existing records using PostgreSQL's function
    conn = op.get_bind()

    # Use a PostgreSQL function to generate UUIDs for each row
    # If you specifically need UUID v6, you may need an extension
    conn.execute(text("""
        UPDATE team_memberships 
        SET membership_id = gen_random_uuid()
        WHERE membership_id IS NULL
    """))

    # Make the membership_id column NOT NULL after populating values
    op.alter_column('team_memberships', 'membership_id', nullable=False)

    # Add primary key constraint to membership_id
    op.execute('ALTER TABLE team_memberships DROP CONSTRAINT team_memberships_pkey')
    op.create_primary_key('team_memberships_pkey', 'team_memberships', ['membership_id'])

    # Create unique constraint on team_id + user_id + org_id
    op.create_unique_constraint('uq_team_user', 'team_memberships', ['team_id', 'user_id'])

    # Modify existing columns to be nullable since they're no longer part of the primary key
    op.alter_column('team_memberships', 'team_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.alter_column('team_memberships', 'user_id',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    # Remove the unique constraint first
    op.drop_constraint('uq_team_user', 'team_memberships', type_='unique')

    # Make the original primary key columns NOT NULL
    op.alter_column('team_memberships', 'user_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('team_memberships', 'team_id',
               existing_type=sa.UUID(),
               nullable=False)

    # Drop the new primary key and restore the original
    op.execute('ALTER TABLE team_memberships DROP CONSTRAINT team_memberships_pkey')
    op.create_primary_key('team_memberships_pkey', 'team_memberships', ['team_id', 'user_id'])

    # Finally, drop the membership_id column
    op.drop_column('team_memberships', 'membership_id')
from typing import Sequence, Union
from uuid import UUID
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, text

# revision identifiers, used by Alembic.
revision: str = 'fcf4d2f6c378'
down_revision: Union[str, None] = '348b71997440'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Define the team_roles table structure
    team_roles = table(
        'team_roles',
        column('role_id', sa.UUID),
        column('name', sa.String),
        column('description', sa.String),
        column('role_slug', sa.String),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )

    # Establish a connection
    conn = op.get_bind()

    # Check if the team_roles table is empty
    result = conn.execute(text("SELECT COUNT(*) FROM team_roles"))
    count = result.scalar()

    if count == 0:
        # Insert the required team role data
        op.bulk_insert(
            team_roles,
            [
                {
                    'role_id': UUID('1f01b47e-d9ad-657a-af49-2708e212442f'),
                    'name': 'Owner',
                    'description': 'Owner of the team',
                    'role_slug': 'owner'
                },
                {
                    'role_id': UUID('1f01b47f-5ea0-61ba-9c9e-2573efbeeffb'),
                    'name': 'Member',
                    'description': 'Member of the team',
                    'role_slug': 'member'
                }
            ]
        )

def downgrade() -> None:
    # Define the team_roles table structure
    team_roles = table(
        'team_roles',
        column('role_id', sa.UUID)
    )

    # Establish a connection
    conn = op.get_bind()

    # Delete the specific roles inserted during upgrade
    conn.execute(
        text("""
            DELETE FROM team_roles
            WHERE role_id IN (
                '1f01b47e-d9ad-657a-af49-2708e212442f',
                '1f01b47f-5ea0-61ba-9c9e-2573efbeeffb'
            )
        """)
    )

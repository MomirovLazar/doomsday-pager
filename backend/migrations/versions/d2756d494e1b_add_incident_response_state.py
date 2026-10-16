"""add incident response state

Revision ID: d2756d494e1b
Revises: 520b7e528e38
Create Date: 2026-10-16 14:34:48.999406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd2756d494e1b'
down_revision: Union[str, Sequence[str], None] = '520b7e528e38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "incident_acknowledgements",
        sa.Column("response", sa.String(20), nullable=True)
    )

    op.add_column(
        "incident_acknowledgements",
        sa.Column(
            "responded_at",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.alter_column(
        "incident_acknowledgements",
        "acknowledged_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True
    )

    #Preserve existing acknowledgement records.

    op.execute(
        """UPDATE incident_acknowledgements 
        SET response = 'ACKNOWLEDGED',
            responded_at = acknowledged_at
    """)

    op.alter_column(
        "incident_acknowledgements",
        "response",
        existing_type=sa.String(20),
        nullable=False
    )

    op.alter_column(
        "incident_acknowledgements",
        "responded_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False
    )

    op.create_check_constraint(
        "ck_incident_response",
        "incident_acknowledgements",
        "response IN ('ACKNOWLEDGED', 'UNAVAILABLE')"
    )

def downgrade() -> None:
    connection = op.get_bind()

    unavailable_exists = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1
                FROM incident_acknowledgements
                WHERE response = 'UNAVAILABLE'
            )
        """)
    ).scalar()

    if unavailable_exists:
        raise RuntimeError(
            "Cannot downgrade while UNAVAILABLE responses exist"
        )

    op.drop_constraint(
        "ck_incident_response",
        "incident_acknowledgements",
        type="check"
    )

    op.alter_column(
        "incident_acknowledgements",
        "acknowledged_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False
    )

    op.drop_column(
        "incident_acknowledgements",
        "responded_at"
    )

    op.drop_column(
        "incident_acknowledgements",
        "response"
    )
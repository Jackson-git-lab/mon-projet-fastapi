"""add colum  owner_id by player

Revision ID: 4c1c2ef28185
Revises: 
Create Date: 2026-01-22 09:06:00.761138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c1c2ef28185'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ajout la colonne owner_id à la table Players
    op.add_column('Players', sa.Column('owner_id', sa.Integer(), nullable=False))
    
    # creation de la clé étrangère vers Users.id
    op.create_foreign_key(
        'fk_players_owner_id',  # nom de la contrainte
        'Players',              # table source
        'Users',                # table cible
        ['owner_id'],           # colonne source
        ['id']                  # colonne cible
    )


def downgrade() -> None:
    """Downgrade schema."""
    # supprime la clé étrangère
    op.drop_constraint('fk_players_owner_id', 'Players', type_='foreignkey')
    
    # supprime la colonne owner_id
    op.drop_column('Players', 'owner_id')

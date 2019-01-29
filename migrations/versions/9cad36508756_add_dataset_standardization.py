"""add dataset standardization

Revision ID: 9cad36508756
Revises: abab2485d66e
Create Date: 2019-01-28 16:07:01.070911

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9cad36508756'
down_revision = 'abab2485d66e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dataset', sa.Column('standardized', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dataset', 'standardized')
    # ### end Alembic commands ###

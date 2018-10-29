"""empty message

Revision ID: 7731946339c5
Revises: 642c21265435
Create Date: 2018-10-25 10:53:33.441343

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7731946339c5'
down_revision = '642c21265435'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('compound', sa.Column('curated_compound', sa.Boolean(), nullable=True))
    op.drop_column('compound', 'new_compound')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('compound', sa.Column('new_compound', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.drop_column('compound', 'curated_compound')
    # ### end Alembic commands ###
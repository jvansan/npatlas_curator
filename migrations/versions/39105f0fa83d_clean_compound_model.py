"""Clean compound model

Revision ID: 39105f0fa83d
Revises: 7c3fb6c4245b
Create Date: 2018-11-13 10:31:57.416966

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '39105f0fa83d'
down_revision = '7c3fb6c4245b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('compound', 'cid')
    op.drop_column('compound', 'cbid')
    op.drop_column('compound', 'csid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('compound', sa.Column('csid', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('compound', sa.Column('cbid', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('compound', sa.Column('cid', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    # ### end Alembic commands ###

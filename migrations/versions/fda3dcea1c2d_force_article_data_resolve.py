"""force_article+data_resolve

Revision ID: fda3dcea1c2d
Revises: 03ed48e49803
Create Date: 2019-02-11 14:56:46.171000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fda3dcea1c2d'
down_revision = '03ed48e49803'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('compound_name')
    op.add_column('checker_article', sa.Column('resolved', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('checker_article', 'resolved')
    op.create_table('compound_name',
    sa.Column('compound_name_id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('compound_name_insert_date', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('compound_name_name', mysql.VARCHAR(length=2000), nullable=False),
    sa.PrimaryKeyConstraint('compound_name_id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###

"""empty message

Revision ID: 93bacd382830
Revises: 29e73bf8196d
Create Date: 2018-08-30 09:20:13.017962

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93bacd382830'
down_revision = '29e73bf8196d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dataset', sa.Column('last_article_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'dataset', 'article', ['last_article_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'dataset', type_='foreignkey')
    op.drop_column('dataset', 'last_article_id')
    # ### end Alembic commands ###

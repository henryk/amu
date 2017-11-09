"""Add invitation owners

Revision ID: 2c669d7ec424
Revises: 8665129c1122
Create Date: 2016-11-21 18:03:25.174432

"""

# revision identifiers, used by Alembic.
revision = '2c669d7ec424'
down_revision = '8665129c1122'

from alembic import op
import sqlalchemy as sa
from ode.blueprints.isi.model import Json


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('invitation', schema=None) as batch_op:
    	batch_op.add_column(sa.Column('owners', Json(), default=[]))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('invitation', schema=None) as batch_op:
    	batch_op.drop_column('owners')
    ### end Alembic commands ###
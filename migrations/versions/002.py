"""Fix migration chain and add cart/webhook/user changes

Revision ID: 002
Revises: 001
Create Date: 2025-11-12 22:25:10.576513

"""
import sqlalchemy as sa
from alembic import op

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('webhook',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('cart',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('cart_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cart_id', sa.Integer(), nullable=False),
        sa.Column('file_model_id', sa.Integer(), nullable=False), 
        sa.ForeignKeyConstraint(['cart_id'], ['cart.id'], ),
        sa.ForeignKeyConstraint(['file_model_id'], ['file_model.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('orcid_id', sa.String(length=32), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_orcid_id'), ['orcid_id'], unique=True)
        batch_op.alter_column('email', existing_type=sa.String(length=256), nullable=True)
        batch_op.alter_column('password', existing_type=sa.String(length=256), nullable=True)


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password', existing_type=sa.String(length=256), nullable=False)
        batch_op.alter_column('email', existing_type=sa.String(length=256), nullable=False)
        batch_op.drop_index(batch_op.f('ix_user_orcid_id'))
        batch_op.drop_column('orcid_id')

    op.drop_table('cart_item')
    op.drop_table('cart')
    op.drop_table('webhook')
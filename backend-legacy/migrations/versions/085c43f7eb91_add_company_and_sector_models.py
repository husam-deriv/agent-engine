"""Add company and sector models

Revision ID: 085c43f7eb91
Revises: c3619f19dd90
Create Date: 2025-05-10 21:23:03.519270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import datetime


# revision identifiers, used by Alembic.
revision: str = '085c43f7eb91'
down_revision: Union[str, None] = 'c3619f19dd90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sector and company tables
    op.create_table('sectors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sectors_id'), 'sectors', ['id'], unique=False)
    op.create_index(op.f('ix_sectors_name'), 'sectors', ['name'], unique=True)
    
    op.create_table('companies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('sector_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['sector_id'], ['sectors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_id'), 'companies', ['id'], unique=False)
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=True)
    
    # Create default sector for existing projects
    # Define sector and company tables for insert
    sectors = table('sectors',
                    column('id', sa.Integer),
                    column('name', sa.String),
                    column('description', sa.Text),
                    column('created_at', sa.DateTime),
                    column('updated_at', sa.DateTime))
    
    companies = table('companies',
                     column('id', sa.Integer),
                     column('name', sa.String),
                     column('sector_id', sa.Integer),
                     column('description', sa.Text),
                     column('created_at', sa.DateTime),
                     column('updated_at', sa.DateTime))
    
    now = datetime.datetime.utcnow()
    
    # Insert default sector
    op.bulk_insert(sectors,
                  [{'id': 1, 
                    'name': 'Default Sector', 
                    'description': 'Default sector for existing projects',
                    'created_at': now,
                    'updated_at': now}])
    
    # Insert default company
    op.bulk_insert(companies,
                  [{'id': 1, 
                    'name': 'Gargash Group', 
                    'sector_id': 1,
                    'description': 'Default company for existing projects',
                    'created_at': now,
                    'updated_at': now}])
    
    # Add nullable company_id column first
    op.add_column('projects', sa.Column('company_id', sa.Integer(), nullable=True))
    
    # Update existing projects to use default company
    op.execute('UPDATE projects SET company_id = 1')
    
    # Now add the foreign key constraint and not null constraint
    op.create_foreign_key('fk_projects_company', 'projects', 'companies', ['company_id'], ['id'])
    op.alter_column('projects', 'company_id', existing_type=sa.Integer(), nullable=False)
    
    # Add the rest of the columns
    op.create_table('data_corpuses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('file_path', sa.String(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.Column('sector_id', sa.Integer(), nullable=True),
    sa.Column('is_sector_wide', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['sector_id'], ['sectors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_corpuses_id'), 'data_corpuses', ['id'], unique=False)
    op.create_index(op.f('ix_data_corpuses_name'), 'data_corpuses', ['name'], unique=False)
    
    op.add_column('projects', sa.Column('is_scheduled', sa.Boolean(), nullable=True))
    op.add_column('projects', sa.Column('schedule_frequency', sa.String(), nullable=True))
    op.add_column('projects', sa.Column('slack_channel', sa.String(), nullable=True))
    op.drop_column('projects', 'target_date')


def downgrade() -> None:
    """Downgrade schema."""
    # Add target_date back
    op.add_column('projects', sa.Column('target_date', sa.DATETIME(), nullable=True))
    
    # Remove columns added in upgrade
    op.drop_constraint('fk_projects_company', 'projects', type_='foreignkey')
    op.drop_column('projects', 'slack_channel')
    op.drop_column('projects', 'schedule_frequency')
    op.drop_column('projects', 'is_scheduled')
    op.drop_column('projects', 'company_id')
    
    # Drop data_corpuses table and indexes
    op.drop_index(op.f('ix_data_corpuses_name'), table_name='data_corpuses')
    op.drop_index(op.f('ix_data_corpuses_id'), table_name='data_corpuses')
    op.drop_table('data_corpuses')
    
    # Drop companies table and indexes
    op.drop_index(op.f('ix_companies_name'), table_name='companies')
    op.drop_index(op.f('ix_companies_id'), table_name='companies')
    op.drop_table('companies')
    
    # Drop sectors table and indexes
    op.drop_index(op.f('ix_sectors_name'), table_name='sectors')
    op.drop_index(op.f('ix_sectors_id'), table_name='sectors')
    op.drop_table('sectors')

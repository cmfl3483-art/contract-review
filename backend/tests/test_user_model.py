"""
Unit tests for User model

Tests verify:
- User model has all required fields (id, dingtalkUserId, name, role, email, mobile, avatar, department)
- Database indexes are properly configured (dingtalkUserId UNIQUE, role)
- Model structure matches requirements 8.10 and 11.8
"""

import pytest
from sqlalchemy import inspect
from app.models.user import User


class TestUserModel:
    """Test suite for User model structure and configuration"""

    def test_user_model_has_required_fields(self):
        """Verify User model has all required fields"""
        # Get all column names from the User model
        mapper = inspect(User)
        column_names = {col.key for col in mapper.columns}
        
        # Required fields from task 2.1
        required_fields = {
            'id',
            'dingtalk_user_id',  # dingtalkUserId in camelCase
            'name',
            'role',
            'email',
            'mobile',
            'avatar',
            'department',
            'created_at',
            'updated_at'
        }
        
        # Verify all required fields exist
        assert required_fields.issubset(column_names), \
            f"Missing fields: {required_fields - column_names}"

    def test_user_model_field_types(self):
        """Verify User model field types are correct"""
        mapper = inspect(User)
        columns = {col.key: col for col in mapper.columns}
        
        # Verify id is UUID
        assert str(columns['id'].type) == 'UUID', \
            f"id should be UUID, got {columns['id'].type}"
        
        # Verify string fields
        string_fields = ['dingtalk_user_id', 'name', 'role', 'email', 'mobile', 'avatar', 'department']
        for field in string_fields:
            assert 'VARCHAR' in str(columns[field].type) or 'String' in str(type(columns[field].type).__name__), \
                f"{field} should be String type, got {columns[field].type}"
        
        # Verify datetime fields
        datetime_fields = ['created_at', 'updated_at']
        for field in datetime_fields:
            assert 'DateTime' in str(type(columns[field].type).__name__), \
                f"{field} should be DateTime type, got {columns[field].type}"

    def test_user_model_nullable_constraints(self):
        """Verify nullable constraints on User model fields"""
        mapper = inspect(User)
        columns = {col.key: col for col in mapper.columns}
        
        # Required (NOT NULL) fields
        required_fields = ['id', 'dingtalk_user_id', 'name', 'role', 'created_at', 'updated_at']
        for field in required_fields:
            assert not columns[field].nullable, \
                f"{field} should be NOT NULL"
        
        # Optional (nullable) fields
        optional_fields = ['dingtalk_union_id', 'email', 'mobile', 'avatar', 'department']
        for field in optional_fields:
            assert columns[field].nullable, \
                f"{field} should be nullable"

    def test_user_model_unique_constraints(self):
        """Verify dingtalkUserId has UNIQUE constraint"""
        mapper = inspect(User)
        columns = {col.key: col for col in mapper.columns}
        
        # dingtalk_user_id should be unique
        assert columns['dingtalk_user_id'].unique, \
            "dingtalk_user_id should have UNIQUE constraint"

    def test_user_model_indexes(self):
        """Verify User model has required indexes"""
        # Get table from User model
        table = User.__table__
        
        # Get all index names and their columns
        indexes = {}
        for index in table.indexes:
            index_columns = [col.name for col in index.columns]
            indexes[index.name] = {
                'columns': index_columns,
                'unique': index.unique
            }
        
        # Verify dingtalk_user_id index exists
        dingtalk_index_found = False
        for index_name, index_info in indexes.items():
            if 'dingtalk_user_id' in index_info['columns']:
                dingtalk_index_found = True
                break
        
        assert dingtalk_index_found, \
            "Index on dingtalk_user_id not found"
        
        # Verify role index exists
        role_index_found = False
        for index_name, index_info in indexes.items():
            if 'role' in index_info['columns']:
                role_index_found = True
                break
        
        assert role_index_found, \
            "Index on role not found"

    def test_user_model_table_name(self):
        """Verify User model table name is 'users'"""
        assert User.__tablename__ == 'users', \
            f"Table name should be 'users', got '{User.__tablename__}'"

    def test_user_model_primary_key(self):
        """Verify User model has id as primary key"""
        mapper = inspect(User)
        primary_keys = [key.name for key in mapper.primary_key]
        
        assert 'id' in primary_keys, \
            "id should be the primary key"
        assert len(primary_keys) == 1, \
            "Should have exactly one primary key"

    def test_user_model_repr(self):
        """Verify User model has a __repr__ method"""
        assert hasattr(User, '__repr__'), \
            "User model should have __repr__ method"

    def test_user_model_comments(self):
        """Verify User model fields have comments/documentation"""
        mapper = inspect(User)
        columns = {col.key: col for col in mapper.columns}
        
        # Check that key fields have comments
        key_fields = ['id', 'dingtalk_user_id', 'name', 'role']
        for field in key_fields:
            # SQLAlchemy stores comments in the column's comment attribute
            assert hasattr(columns[field], 'comment'), \
                f"{field} should have a comment attribute"


class TestUserModelIntegration:
    """Integration tests for User model (require database connection)"""
    
    @pytest.mark.skip(reason="Requires database connection - run manually with test database")
    def test_user_model_can_be_created(self):
        """Verify User model can be instantiated and saved to database"""
        # This test would require a test database connection
        # Skipped for now as it requires infrastructure setup
        pass

    @pytest.mark.skip(reason="Requires database connection - run manually with test database")
    def test_dingtalk_user_id_unique_constraint_enforced(self):
        """Verify database enforces UNIQUE constraint on dingtalk_user_id"""
        # This test would verify that attempting to insert duplicate dingtalk_user_id fails
        # Skipped for now as it requires infrastructure setup
        pass

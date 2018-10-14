from logging import getLogger
from sqlalchemy.exc import IntegrityError
from auth_server import db_wrapper
from auth_server.models.errors import DoesNotExist, DuplicateConstraint


class CrudModel:
    """Mixin to be used with FlaskSqlAlchemy model class to add CRUD operations"""
    @classmethod
    def get_by_id(cls, id):
        """get a row by id

        :raises DoesNotExist: in case the resource does not exist.
        """
        record = cls.query.filter_by(id=id).first()
        if record is None:
            raise DoesNotExist
        return record

    @classmethod
    def get_all(cls):
        """get all rows"""
        return cls.query.all()

    @classmethod
    def create(cls, data: dict):
        """Insert a new record and returns the id"""
        instance = cls(**data)
        db_wrapper.session.add(instance)
        try:
            db_wrapper.session.commit()
        except IntegrityError as e:
            getLogger().exception(e)
            db_wrapper.session.rollback()
            raise DuplicateConstraint
        except Exception as e:
            db_wrapper.session.rollback()
            raise e
        return instance.id

    @classmethod
    def update(cls, id, data: dict):
        """Update a record partially

        :raises DoesNotExist: if provided id does not exist in database.
        """
        try:
            count = db_wrapper.session.query(cls).filter(cls.id == id).update(data)
        except IntegrityError as e:
            getLogger().exception(e)
            db_wrapper.session.rollback()
            raise DuplicateConstraint
        try:
            db_wrapper.session.commit()
        except Exception as e:
            db_wrapper.session.rollback()
            raise e
        if count == 0:
            raise DoesNotExist

    @classmethod
    def delete(cls, id):
        """Delete a record by the provided id

        :raises DoesNotExist: in case the resource does not exist.
        """
        count = cls.query.filter_by(id=id).delete()
        if count == 0:
            raise DoesNotExist

from auth_server import create_app, db_wrapper


app = create_app({})
db_wrapper.database.create_tables([])
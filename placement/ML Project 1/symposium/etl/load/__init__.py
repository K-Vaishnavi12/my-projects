"""Load stage.

Import loaders directly to avoid pulling pymongo when you only
need SQLite (or vice versa):

    from symposium.etl.load.sqlite_loader import SqliteLoader
    from symposium.etl.load.mongo_loader import MongoLoader
"""

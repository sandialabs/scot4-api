
def main():
    try:
        from app.db.session import SessionLocal
        SessionLocal()
        return 0
    except Exception as e:
        print('Could not connect to SQL database via API code, make sure SCOT4\'s'
                + 'src/ directory is in your PYTHONPATH and that the '
                + 'SQLALCHEMY_DATABASE_URI environment variable is set')
        return 1

if __name__ == '__main__':
    exit(main())

import argparse, sys
from ccj import *
from scripts import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-sdb', '--setupdb', action='store_true', help='Creates all the database models.')
    parser.add_argument('--loudsql', action='store_true', help='Logs all sql executed. Good to double check your queries.')

    args = parser.parse_args()

    if args.loudsql:
        app.config['SQLALCHEMY_ECHO'] = True

    if args.setupdb:
        setup_db(db)
        sys.exit()

    app.run()

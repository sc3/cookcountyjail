import argparse, sys
from ccj import *
from scripts import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-sdb', '--setupdb', action='store_true', help='Creates all the database models')

    args = parser.parse_args()

    if args.setupdb:
        setup_db(db)
        sys.exit()

    app.run()

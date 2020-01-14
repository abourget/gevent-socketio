#!/usr/bin/env python
import os
import sys
from pyramid.config import Configurator

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from testapp.models import Base

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

DBSession = scoped_session(sessionmaker())

here = os.path.dirname(__file__)

def usage(argv):# pragma: no cover 
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv): # pragma: no cover
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)

    config = Configurator(
        settings=settings
    )

    config.include('testapp.models')

    engine = engine_from_config(settings, 'sqlalchemy.')

    Base.metadata.bind = engine
    Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)

if __name__ == "__main__": # pragma: no cover
    main()

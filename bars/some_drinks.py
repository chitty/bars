# -*- coding: utf-8 -*
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Bar, Base, Drink, User

engine = create_engine('sqlite:///bars.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
INITAL_DATA_FILE = 'initial_drinks.json'

try:
    json_drinks = json.loads(open(INITAL_DATA_FILE, 'r').read())
except:
    print 'Unable to read file %s, no data imported!' % INITAL_DATA_FILE
    exit(1)


def insert(element):
    """Inserts the passed element into the database."""
    session.add(element)
    session.commit()

# Create dummy user
user_id = json_drinks['User']['id']
dummy_user = User(id=user_id,
                  name=json_drinks['User']['name'],
                  email=json_drinks['User']['email'],
                  picture=json_drinks['User']['picture'])
insert(dummy_user)

if 'Bars' not in json_drinks:
    print 'No bars found in %s, no data imported!' % INITAL_DATA_FILE
    exit(1)

bars = json_drinks['Bars']
i = 0
j = 0
for bar in bars:
    new_bar = Bar(id=bar['id'], name=bar['name'], user_id=user_id)
    insert(new_bar)
    i = i + 1
    for drink in bar['Drinks']:
        new_drink = Drink(name=drink['name'], price=drink['price'],
                          type=drink['type'], bar=new_bar,
                          description=drink['description'], user_id=user_id)
        insert(new_drink)
        j = j + 1

print "%d bars and %d drinks were inserted!" % (i, j)

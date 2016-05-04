# -*- coding: utf-8 -*
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Bar, Base, Drink, User

engine = create_engine('sqlite:///bars.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create dummy user
User1 = User(name="John Doe", email="johndoe@doemails.com",
             picture='https://lh3.googleusercontent.com/uFp_tsTJboUY7kue5XAsGA')
session.add(User1)
session.commit()

# Menu for Martini Bar
bar1 = Bar(user_id=1, name="Martini Bar")

session.add(bar1)
session.commit()


drink1 = Drink(user_id=1, name="Hendrick's Breakfast Martini", description="1.5 oz Hendrick's Gin, 2 tsp Orange marmalade, .75 oz Fresh lemon juice, .5 oz Simple syrup. Garnish: 1 Lemon Peel Glass: Cocktail",
               price="7.50", type="Cocktail", bar=bar1)

session.add(drink1)
session.commit()

drink2 = Drink(user_id=1, name="Dry Martini", description="The Dry Martini is a classic cocktail that, like a tailored suit, is timeless. Although the original of the tipple is unclear, the Dry Martini has maintained a place in cocktail history due to being easy to use and endlessly sophisticated. Elegant for the fancy and boozy for the heavy-handed.",
               price="6.50", type="Cocktail", bar=bar1)

session.add(drink2)
session.commit()

drink3 = Drink(user_id=1, name="1942 Martini", description="A really good tequila can make a really good Martini.",
               price="5.50", type="Cocktail", bar=bar1)

session.add(drink3)
session.commit()

drink4 = Drink(user_id=1, name="Black Pepper Gibson", description="4oz of Dry vermouth garnished with black-pepper-and-onion making this classic drink a savory delight.",
               price="3.99", type="Cocktail", bar=bar1)

session.add(drink4)
session.commit()

drink5 = Drink(user_id=1, name="You Name it Martini", description="Just ask for any combination you would like to try",
               price="4.99", type="Cocktail", bar=bar1)

session.add(drink5)
session.commit()


# Menu for La Cantina
bar2 = Bar(user_id=1, name="La Cantina")

session.add(bar2)
session.commit()


drink1 = Drink(user_id=1, name="Cuba Libre", description="Perfect match between rum and coke, lots of ice and a bit of lime.",
               price="5.99", type="Cocktail", bar=bar2)

session.add(drink1)
session.commit()

drink2 = Drink(user_id=1, name="Mojito", description="White rum with fresh mint.",
               price="6.25", type="Cocktail", bar=bar2)

session.add(drink2)
session.commit()

drink3 = Drink(user_id=1, name="Tequila a lo Macho", description="Our house finest tequila de la casa, solo para los meros meros machos!",
               price="4.99", type="Shot", bar=bar2)

session.add(drink3)
session.commit()

bar3 = Bar(user_id=1, name="Beer Factory")

session.add(bar3)
session.commit()


drink1 = Drink(user_id=1, name="Red Beer", description="Delicious ice-cold red beer full of flavour.",
               price="1.99", type="Beer", bar=bar3)

session.add(drink1)
session.commit()

drink2 = Drink(user_id=1, name="Honey Beer", description="Ice cold beer blended with the perfect bee honey.",
               price="2.25", type="Beer", bar=bar3)

session.add(drink2)
session.commit()

drink3 = Drink(user_id=1, name="Black Beer", description="Our house finest beer dark, strong and full of flavour",
               price="2.99", type="Beer", bar=bar3)

session.add(drink3)
session.commit()

print "bars and drinks inserted!"

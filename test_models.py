import unittest
from app import app, db  
from models import User, Cocktail

class UserModelTest(unittest.TestCase):

    def setUp(self):
        # Called before every test
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///capstone_1_test'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        # Called after every test
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    

class CocktailModelTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///capstone_1_test'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_cocktail_favorite_toggle(self):
        u = User(username='john')
        u.set_password('johnspassword')
        c = Cocktail(name='Mojito', image_url='http://example.com/mojito.jpg', instructions='Mix and serve.')
        db.session.add(u)
        db.session.add(c)
        db.session.commit()

        # Assert the cocktail is not in the favorites
        self.assertNotIn(c, u.favorite_cocktails)

        # Toggle favorite
        c.toggle_favorite(u)
        self.assertIn(c, u.favorite_cocktails)

        # Toggle favorite again
        c.toggle_favorite(u)
        self.assertNotIn(c, u.favorite_cocktails)

    

if __name__ == "__main__":
    unittest.main()
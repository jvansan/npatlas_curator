from flask import abort, url_for
from flask_testing import TestCase

from app import create_app, db
from app.models import Article, Compound, Curator, Dataset


class TestBase(TestCase):
    """
    Base class for testing database
    Requires "flask_testing" database in MySQL server
    """

    def create_app(self):
        config_name = 'testing'
        app = create_app(config_name)
        app.config.update(SQLALCHEMY_DATABASE_URI='mysql+pymysql://jvansan:jvansan@localhost/flask_testing')
        return app

    def setUp(self):
        """
        Will get called before each test
        """

        # Set-up Test DB
        db.create_all()

        # Create test admin user
        admin = Curator(username='admin', password='admin2018', is_admin=True)

        # Create test non-admin user
        user = Curator(username='test_user', password='test2018')

        # Save users to database
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        """
        Will be called after each test
        """
        db.session.remove()
        db.drop_all()


class TestModels(TestBase):

    def test_curator_model(self):
        # Tests
        self.assertEqual(Curator.query.count(), 2)

    def test_compound_model(self):
        # create compound and add to db
        cmpd = Compound(name='Methane',
                        smiles='C',
                        source_organism='Saccharomyces cerevisiae')
        db.session.add(cmpd)
        db.session.commit()

        # Tests
        self.assertEqual(Compound.query.count(), 1)
        self.assertEqual(Compound.query.first().name, 'Methane')

    def test_article_no_compounds_model(self):
        # create compound and add to db
        art = Article(pmid=12345, journal='Test Journal',
                      year=2018, volume='12', issue='12',
                      pages='1-1000', authors='Douglas Adams',
                      doi='10.1234/HHGTTG', title='HHGTTG',
                      abstract='Test Abstract', num_compounds=0)
        db.session.add(art)
        db.session.commit()


        # Tests
        self.assertEqual(Article.query.count(), 1)
        self.assertEqual(Article.query.first().pmid, 12345)

    def test_article_one_compound_model(self):
        # Create compound
        cmpd = Compound(name='Methane',
                        smiles='C',
                        source_organism='Saccharomyces cerevisiae')
        # Create article with compound
        art = Article(pmid=12345, journal='Test Journal',
                      year=2018, volume='12', issue='12',
                      pages='1-1000', authors='Douglas Adams',
                      doi='10.1234/HHGTTG', title='HHGTTG',
                      abstract='Test Abstract', num_compounds=1,
                      compounds=[cmpd])
        db.session.add(art)
        db.session.commit()

        # Tests
        self.assertEqual(Article.query.count(), 1)
        self.assertEqual(len(Article.query.first().compounds), 1)
        self.assertEqual(Article.query.first().compounds[0].id, 1)

    def test_empty_dataset_model(self):
        """
        Create dataset for test_user with no data
        """
        # Get curator
        curator = Curator.query.filter_by(username='test_user').first()
        self.assertEqual(curator.username, 'test_user')

        # Create empty dataset and add
        ds = Dataset(curator=curator)
        db.session.add(ds)
        db.session.commit()

        # Tests
        self.assertEqual(Dataset.query.count(), 1)
        self.assertEqual(Dataset.query.first().curator_id, 2)
        self.assertEqual(len(Dataset.query.first().articles), 0)

    def test_one_article_no_compounds_dataset_model(self):
        # Create article without compound
        art = Article(pmid=12345, journal='Test Journal',
                      year=2018, volume='12', issue='12',
                      pages='1-1000', authors='Douglas Adams',
                      doi='10.1234/HHGTTG', title='HHGTTG',
                      abstract='Test Abstract', num_compounds=0)

        # Get curator
        curator = Curator.query.filter_by(username='test_user').first()
        self.assertEqual(curator.username, 'test_user')

        # Create empty dataset and add
        ds = Dataset(curator=curator, articles=[art])
        db.session.add(ds)
        db.session.commit()

        # Tests
        self.assertEqual(Dataset.query.count(), 1)
        self.assertEqual(Dataset.query.first().curator.username, 'test_user')
        self.assertEqual(len(Dataset.query.first().articles), 1)
        self.assertEqual(Dataset.query.first().articles[0].pmid, 12345)

    def test_one_article_one_compound_dataset_model(self):
        # Create compound
        cmpd = Compound(name='Methane',
                        smiles='C',
                        source_organism='Saccharomyces cerevisiae')
        # Create article with compound
        art = Article(pmid=12345, journal='Test Journal',
                      year=2018, volume='12', issue='12',
                      pages='1-1000', authors='Douglas Adams',
                      doi='10.1234/HHGTTG', title='HHGTTG',
                      abstract='Test Abstract', num_compounds=1,
                      compounds=[cmpd])

        # Get curator
        curator = Curator.query.filter_by(username='test_user').first()
        self.assertEqual(curator.username, 'test_user')

        # Create empty dataset and add
        ds = Dataset(curator=curator, articles=[art])
        db.session.add(ds)
        db.session.commit()

        # Tests
        self.assertEqual(Dataset.query.count(), 1)
        self.assertEqual(len(Dataset.query.first().articles), 1)
        self.assertEqual(Dataset.query.first().articles[0].pmid, 12345)
        self.assertEqual(len(Dataset.query.first().articles[0].compounds), 1)
        self.assertEqual(Dataset.query.first().articles[0].compounds[0].name, 'Methane')


class TestViews(TestBase):

    def test_homepage_view(self):
        response = self.client.get(url_for('home.homepage'))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.get(url_for('auth.login'))
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        """
        Test that logout link is inaccessible without login
        and redirects to login page
        """
        target_url = url_for('auth.logout')
        redirect_url = url_for('auth.login', next=target_url)
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

    def test_dashboard_view(self):
        """
        Test that dashboard link is inaccessible without login
        and redirects to login page
        """
        target_url = url_for('data.curator_dashboard', cur_id=1)
        redirect_url = url_for('auth.login', next=target_url)
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

    def test_admin_dashboard_view(self):
        """
        Test that admin dashboard link is inaccessible without login
        and redirects to login page
        """
        target_url = url_for('home.admin_dashboard')
        redirect_url = url_for('auth.login', next=target_url)
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

    def test_curators_view(self):
        """
        Test that curators page is inaccessible without admin login
        and redirects to login page
        """
        target_url = url_for('admin.list_curators')
        redirect_url = url_for('auth.login', next=target_url)
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)


class TestErrorPages(TestBase):

    def test_403_forbidden(self):
        # create route to abort requests w 403 Error
        @self.app.route('/403')
        def forbidden_error():
            abort(403)

        response = self.client.get('/403')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(b"403 Error" in response.data)

    def test_404_not_found(self):
        response = self.client.get('/nothinghere')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(b"404 Error" in response.data)

    def test_500_internal_server_error(self):
        # create route to abort requests w 500 Error
        @self.app.route('/500')
        def internal_server_error():
            abort(500)

        response = self.client.get('/500')
        self.assertEqual(response.status_code, 500)
        self.assertTrue(b"500 Error" in response.data)

from django.test import Client, TestCase
from .models import *
#c.post('/match/21/judge',)


class MyTestCase(TestCase):

    def test1(self):
        print('running')

        c = Client()

        c.login(username="admin", password="admin")

        self.assertFalse(c.post("/match/85/judge/", {"advancers": 25}))

from django.test import Client

c = Client()

c.login(username="admin", password="admin")

response = c.post("/match/85/judge/", {"advancers": 25})
print(response)

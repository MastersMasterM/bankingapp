In this project psycopg2 is used for intracting with PostgreSQL

0.Change <<psycopg2.connect(dbname="test", user="postgres", password="ma1379?")>> in

	accounts/db_init.py
	accounts/views.py

with your own setting.

1. Run db_init.py which is located in accounts folder in order to create needed tables and procedures

2. Run <<python manage.py runserver>>

# I didn't change the default setting "db.sqlite3" is being built by default and it's not a part of my project.



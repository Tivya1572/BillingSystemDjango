# BillingSystemDjango
----------- COMMANDS --------------------------------------------

.\billing_env\Scripts\activate -- To activate Virtual Environment
pip install -r requirements.txt   -- to install necessary packages
python manage.py migrate 
python manage.py makemigrations -- to make migrations in db
python manage.py createsuperuser           
python manage.py runserver -- to run the project

------------------------- SAMPLE LINKS TO ACCESS ------------------
"POST /billing/
"GET /billing/history/
"GET /billing/bill/{purchase_id}/
"GET /billing/

-------------------------------------------------------------------



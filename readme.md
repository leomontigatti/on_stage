# On Stage

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/)

On Stage is a Django web application designed to:

- Manage events details such as its start and end dates, place, contact information, categories, prices and schedules.
- View user registration and its related academy, professors and dancers.
- Register different choreographies and seminars participation.
- View registrations costs, discounts and payments.
- Jury users can assign scores, disqualify and record a feedback.
- Academies can view this scores, listen to feedback and print an award certificate.

On Stage uses Django's translation system so the UI will be in *english* or *spanish* depending on your browser language.

> [!NOTE]
> If you would like to skip all the configuration steps and take a look at a working version of the app, you can head to my [On Stage](http://137.184.122.237/) demo server. Its database resets every day with some preloaded data so you can play around and check out its features. All passwords are `123456`.
>
>- Admin account email: `admin@example.com`
>- Judge account email: `judge@example.com`
>- Regular account email: `johndoe@example.com`

## Installation

Create the folder that will hold the app files and enter it.

``` bash
mkdir on_stage
cd on_stage/
```

Copy and paste to clone the project repository.

``` bash
git clone https://github.com/leomontigatti/on_stage.git
```

Some of the libraries used by the app depend on other ones to work properly. We will install all of them just in case anyone is missing.

``` bash
sudo apt update
sudo apt install python3-dev virtualenv redis-server ffmpeg gettext
```

It's recommended to install app-only related dependencies inside a virtual environment. For this we will use *virtualenv* installed previously.

``` bash
virtualenv venv
```

Activate the virtual environment and install the those dependencies.

``` bash
source venv/bin/activate
pip install -r requirements.txt
```

> [!IMPORTANT]
> From now on, some **environment variables** are needed in order to run the app. Please contact me and I will provide them.

## Usage

Most features have their own tests and you can run them by using:

``` bash
python3 manage.py test
```

Run migrations and, for functionality reasons, create the first superuser with the credentials you prefer.

``` bash
python3 manage.py migrate
python3 manage.py createsuperuser
```

Run the web server using:

``` bash
python3 manage.py runserver
```

> [!TIP]
> You should now be able to open your web browser, navigate to [localhost](http://127.0.0.1:8000/) and start using the app.

*While DEBUG is set to* ```True``` *some features that depend on Celery to be running, like sending activation emails or updating prices, are disabled.*

1. Log in using the superuser credentials you set before.
2. Create a new **Contact** and a new **Event** setting its start and end dates.
3. Create as many new **Categories**, **Dance modes**, **Prices** and **Schedules** as you like. While doing this, keep in mind that:
    - Category and Price depend on each other (if you create a 'solo' category, create a price for that category type).
    - Dance mode and Schedule depend on each other as well.
4. You could now log out and register a regular account using the sign up link.
5. That should be it, you can now log in to that account and start using the app.

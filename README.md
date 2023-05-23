# TimeEnjoyedEvents
Discord/Twitch Bots and API servers for TimeEnjoyed Events.


## Installation
- **Please make sure you have Python 3.10+**
- **Install PostgreSQL on your system.**
  - Create a database user and database (Note them down for later)


**Run the following command from within an activated virtual environment of Python 3.10+:**
```shell
pip install -U -r requirements.txt
```

## Config
- Create a file: `config.toml` and copy and paste the contents from `config.example.toml`
- Fill out the dsn for the database with the details from earlier.
- Create a Discord Application and Bot. Generate a token and put it in your `config.toml` under tokens.


## Running
- Run each service separately by running the respective `launcher.py` in each directory.
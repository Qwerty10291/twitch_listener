from flask import Flask, render_template
from sqlalchemy.orm import session
from db import db_session, models
from db import logic as db

db_session.global_init()
import os

import gevent.monkey
from celery import Celery
from flask import Flask
from flask_login.login_manager import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads

from common import config
from src.definitions import INPUT_APK_DIR

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = config.MYSQL_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.secret_key = os.urandom(24)
login_manager = LoginManager(app)

app.config['UPLOADED_APKS_DEST'] = INPUT_APK_DIR
apks = UploadSet('apks', ('apk',))
configure_uploads(app, (apks,))

app.config['CELERY_BROKER_URL'] = config.RABBITMQ_URL
app.config['CELERY_ROUTES'] = {
    'static_analysis_task': {'queue': 'static_queue'},
    'dynamic_analysis_task': {'queue': 'dynamic_queue'}}
app.config['CELERYD_PREFETCH_MULTIPLIER'] = 1
app.config['CELERY_ACKS_LATE'] = True



gevent.monkey.patch_all()
socketio = SocketIO(app, message_queue=config.RABBITMQ_URL)


def make_celery(app):
    celery = Celery(broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)


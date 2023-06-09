import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
import json

import amqp_setup
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)  


class Activity(db.Model):
    __tablename__ = 'activity'

    activityID = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(255), nullable=False)
    activity_info = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())

    def json(self):
        dto = {
            'activityID': self.activityID,
            'activity_type': self.activity_type,
            'activity_info': self.activity_info,
            'timestamp': self.timestamp
        }

        return dto



monitorBindingKey='#'

def receiveActivityLog():
    amqp_setup.check_setup()
    
    queue_name = 'Activity_Log'
    
    # set up a consumer and start to wait for coming messages
    amqp_setup.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    amqp_setup.channel.start_consuming() # an implicit loop waiting to receive messages; 
    #it doesn't exit by default. Use Ctrl+C in the command window to terminate it.

def callback(channel, method, properties, body): # required signature for the callback; no return
    print("\nReceived an actiivity log by " + __file__)
    processActivityLog(json.loads(body))
    print() # print a new line feed

def processActivityLog(activity):
    print("Recording an activity log:")
    print(activity)

    activity = Activity(activity_type=activity["type"], activity_info=activity["info"], timestamp=datetime.now())
    db.session.add(activity)
    db.session.commit()
    db.session.close()


if __name__ == "__main__":  # execute this program only if it is run as a script (not by 'import')
    with app.app_context():
        print("\nThis is " + os.path.basename(__file__), end='')
        print(": monitoring routing key '{}' in exchange '{}' ...".format(monitorBindingKey, amqp_setup.exchangename))
        receiveActivityLog()

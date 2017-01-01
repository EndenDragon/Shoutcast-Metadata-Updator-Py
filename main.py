from config import config
from database import db, Properties
from flask import Flask, Response, g, redirect, request, url_for
from lxml import etree
import datetime
import requests
import time

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = config['DATABASE_URI']
app.config['SQLALCHEMY_POOL_RECYCLE'] = 250

db.init_app(app)

def getMetadata():
    p = requests.get(config['shoutcast-metadata-url'])
    parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
    x = etree.fromstring(str(p.text), parser=parser)
    return x

def getBotListeners():
    q = Properties.query.filter_by(name='botListeners').first()
    if q is None:
        prop = Properties(name="botListeners", value="0")
        db.session.add(prop)
        db.session.commit()
        q = Properties.query.filter_by(name='botListeners').first()
    return int(q.value)

def setBotListeners(value):
    q = Properties.query.filter_by(name='botListeners').first()
    if q is None:
        prop = Properties(name="botListeners", value=str(value))
        db.session.add(prop)
    else:
        q.value = str(value)
    db.session.commit()

def getLastUpdate():
    q = Properties.query.filter_by(name='lastUpdate').first()
    if q is None:
        prop = Properties(name="lastUpdate", value="0")
        db.session.add(prop)
        db.session.commit()
        q = Properties.query.filter_by(name='lastUpdate').first()
    return float(q.value)

def setLastUpdate(value):
    q = Properties.query.filter_by(name='lastUpdate').first()
    if q is None:
        prop = Properties(name="lastUpdate", value=str(value))
        db.session.add(prop)
    else:
        q.value = str(value)
    db.session.commit()

@app.route("/", methods=['GET'])
def page_get():
    botListeners = getBotListeners()
    lastUpdate = getLastUpdate()
    now = time.time()
    if (botListeners is None or botListeners == 0) or now - lastUpdate > 30:
        meta = getMetadata()
        #fix brackets in metadata
        for elem in meta.xpath('/SHOUTCASTSERVER/SONGTITLE'):
            if elem.text is not None and "[" in elem.text and (len(elem.text[elem.text.rfind('['):elem.text.rfind(']') + 1]) == 5):
                elem.text = elem.text[:elem.text.rfind('[')]
        res = etree.tostring(meta)
        return Response(res, mimetype='text/xml')
    else:
        meta = getMetadata()
        for elem in meta.xpath('/SHOUTCASTSERVER/CURRENTLISTENERS'):
            if elem.text is not None:
                elem.text = str(int(elem.text) + int(botListeners))
        for elem in meta.xpath('/SHOUTCASTSERVER/UNIQUELISTENERS'):
            if elem.text is not None:
                elem.text = str(int(elem.text) + int(botListeners))
        #fix brackets in metadata
        for elem in meta.xpath('/SHOUTCASTSERVER/SONGTITLE'):
            if elem.text is not None and "[" in elem.text and (len(elem.text[elem.text.rfind('['):elem.text.rfind(']') + 1]) == 5):
                elem.text = elem.text[:elem.text.rfind('[')]
        res = etree.tostring(meta)
        return Response(res, mimetype='text/xml')

@app.route("/", methods=['POST'])
def page_post():
    if request.form['key'] in config['api-key']:
        setLastUpdate(time.time())
        setBotListeners(request.form['count'])
    return redirect(url_for('page_get'))

if __name__ == "__main__":
    app.run(host=config['ip'],port=config['port'],debug=config['debug'])

from config import config
from flask import Flask, Response, redirect, request, url_for
from flask_redis import FlaskRedis
from lxml import etree
import logging
import requests
import time

app = Flask(__name__)

app.config['REDIS_URL'] = config["redis-uri"]
redis_store = FlaskRedis(charset="utf-8", decode_responses=True)
redis_store.init_app(app)

# Disable HTTP Connection messages from requests
logging.getLogger("requests").setLevel(logging.WARNING)

def getMetadata():
    p = requests.get(config['shoutcast-metadata-url'])
    utf = u''.join(p.text).encode('utf-8')
    parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
    x = etree.fromstring(utf, parser=parser)
    return x

def getBotListeners():
    value = redis_store.get("shoutcast/botListeners")
    if not value:
        value = 0
    return int(value)

def setBotListeners(value):
    redis_store.set("shoutcast/botListeners", value)

def getLastUpdate():
    value = redis_store.get("shoutcast/lastUpdate")
    if not value:
        value = 0
    return float(value)

def setLastUpdate(value):
    redis_store.set("shoutcast/lastUpdate", str(value))

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

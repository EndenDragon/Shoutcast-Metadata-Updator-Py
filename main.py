from config import config
from flask import Flask, Response, g, redirect, request, url_for
from lxml import etree
import datetime
import requests
import time

app = Flask(__name__)
botListeners = 0
lastUpdate = 0

def getMetadata():
    p = requests.get(config['shoutcast-metadata-url'])
    parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
    x = etree.fromstring(str(p.text), parser=parser)
    return x

@app.route("/", methods=['GET'])
def page_get():
    global botListeners, lastUpdate
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
        global botListeners, lastUpdate
        lastUpdate = time.time()
        botListeners = request.form['count']
    return redirect(url_for('page_get'))

if __name__ == "__main__":
    app.run(host=config['ip'],port=config['port'],debug=config['debug'])

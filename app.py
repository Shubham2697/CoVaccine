from flask import Flask, render_template, url_for, request, redirect
import datetime
import pandas as pd
import numpy as np

import requests as req
import json
import re


app = Flask(__name__)

base_url = 'https://cdn-api.co-vin.in/api/'

header_df = ['Date', 'Center Code & Name', 'Address', 'District Name', 'State Name', 'Pincode',
        'Time', 'Paid/Free', 'Minimum Age', 'Available slots', 'Vaccine', 'session_id', 'Slots', 'Vaccine fees']

def rq(url):
    print(url)
    h = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        }
    r = req.get(
        url, 
        headers = h, 
        )
    print(r, r.headers)
    return r

@app.route('/', methods = ['GET', 'POST'])
def index():
    POST_CODE = 110001
    DIST_ID = 1

    age = 100
    numdays = 1

    base_date = datetime.datetime.today()
    date_str =[(base_date + datetime.timedelta(days=x)).strftime("%d-%m-%Y") for x in range(numdays)]

    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':

        if 'back' in request.form.keys():
            return render_template('index.html')
        
        try:
            age = int(request.form['age'])
        except:
            age = 100
        try:
            numdays = int(request.form['numdays'])
        except:
            numdays = 1


        if 'pincode' in request.form.keys() or 'dist' in request.form.keys():
            if str(request.form['enter_code']) != '':
                CODE = str(request.form['enter_code'])
            else:
                return render_template('index.html')

            if 'pincode' in request.form.keys():
                url = "v2/appointment/sessions/public/calendarByPin?pincode={}&date=".format(CODE)
            elif  'dist' in request.form.keys():
                url = "v2/appointment/sessions/public/calendarByDistrict?district_id={}&date=".format(CODE)
            
            l =[]
            for INP_DATE in date_str:
                URL = base_url + url + INP_DATE
                response = rq(URL)
                if response.ok:
                    resp_json = response.json()
                    if resp_json["centers"]:
                        for center in resp_json["centers"]:
                            for session in center["sessions"]:
                                if INP_DATE==session['date']:
                                    l.append([
                                        session['date'], 
                                        str(center["center_id"]) + ' : '+ center["name"],
                                        center["block_name"] + " : " + center["name"] + ", " + center["address"].title() + ', ' + center['district_name'] + ', ' + center['state_name'],
                                        center['district_name'], 
                                        center['state_name'], 
                                        center['pincode'],
                                        center['from'] + ' to ' + center['to'], 
                                        center['fee_type'], 
                                        session["min_age_limit"], 
                                        session['available_capacity'], 
                                        session['vaccine'], 
                                        session['session_id'],
                                        str(len(session['slots'])) + ' : ' + ', '.join(session['slots']),
                                        None
                                    ])
                                    try:
                                        l[-1][-1] = ', '.join([i['vaccine'] + ' : ' + i['fee'] for i in center['vaccine_fees']])
                                    except:
                                        pass

                df = pd.DataFrame(l, columns=header_df).drop_duplicates().drop('session_id', axis=1)
                # df = df[df['Available slots']>0]
                df = df.astype({'Minimum Age':int})
                df = df[df['Minimum Age']<=age]

                return render_template("table.html", table=df.to_html(classes='data', header=True, index=False))
        elif 'distcodes' in request.form.keys():
            states = rq(base_url + 'v2/admin/location/states')
            s = []
            if states.ok:
                states = states.json()
                # print(json.dumps(states, indent=2))
                for state in states['states']:
                    distiricts = rq(base_url + 'v2/admin/location/districts/{}'.format(state['state_id']))
                    if distiricts.ok:
                        distiricts = distiricts.json()
                        # print(json.dumps(distiricts, indent=2))
                        for district in distiricts['districts']:
                            s.append([state['state_name'], state['state_id'], district['district_name'], district['district_id']])
                
            df = pd.DataFrame(s, columns=['State Name', 'State ID', 'District Name', 'District ID']).sort_values(by = ['State Name', 'District ID'])
            return render_template("table.html", table=df.to_html(classes='data', header=True, index=False))

if __name__=="__main__":
    app.run(debug=True)
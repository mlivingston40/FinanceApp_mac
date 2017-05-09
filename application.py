# -*- coding: utf-8 -*-
"""
	Finance App
	~~~~~~
	A stock modelling application.
	:copyright: (c) 2017
"""


from flask import Flask, render_template, request, redirect, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, BooleanField, validators
from wtforms.validators import DataRequired, Email, InputRequired
from flask_mail import Mail, Message
from wtforms import DateField
from wtforms.fields.html5 import DateField
from datetime import datetime, date
from Modules.model import *
from bokeh.embed import components

app = Flask(__name__)
app.secret_key = 'donttellnobody'


class StockForm(FlaskForm):
    stock = StringField('Stock', [validators.DataRequired("Please enter a stock name.")])
    date_start = DateField('Start Date')
    date_end = DateField('End Date')

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/timedecay', methods = ['GET','POST'])
def timedecay():

	form = StockForm()

	if request.method == 'POST':

		try:

			security = request.form['stock']
			start_date = request.form['date_start']
			end_date = request.form['date_end']

			a = TimeDecaySeries(security, start_date, end_date)

			p = a.close_prices_graph()
			div, script = components(p)

			s = a.gains_summary_graph()
			div2, script2 = components(s)

			#d = a.dropdown()
			#div3, script3 = components(d)

			d = a.testing()
			div3, script3 = components(d)

			return render_template("results.html", script=script, div=div, script2=script2, div2=div2,
								   script3=script3, div3=div3)

		except:
			return "Please go back and submit correctly"

	elif request.method == 'GET':

		return render_template('timedecay.html', form=form)

#else:	#return render_template('timedecay.html', form=form)


#some routing testing





@app.route('/examples')
def examples():
	return render_template('examples.html')



app.run(debug=True)

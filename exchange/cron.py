# -*- coding: utf-8 -*- 
import csv
from django.http import HttpResponse
from .models import Exchange
import json
import quandl
import datetime
import urllib2
import pytz

#set api key
quandl.ApiConfig.api_key = 'QWTqFXgs58dsasdnEqE7' #my account

def getExchangeRate(code, start_date):
	url = 'https://www.quandl.com/api/v3/datasets/CURRFX/USD' + code + '.json?api_key=' + quandl.ApiConfig.api_key + '&start_date=' + start_date
	
	# 쿼리 전송 
	user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
	headers = { 'User-Agent' : user_agent }
	r = urllib2.Request(url, headers=headers)
	url_source = urllib2.urlopen(r).read()
	exchangeRate_json = json.loads(url_source)

	# 데이터 추출 
	exchangeRates = exchangeRate_json['dataset']['data']
	exchangeRates.reverse() # 오름차순 정렬 

	return exchangeRates

def my_scheduled_job():
	tz = pytz.timezone('Asia/Seoul')
	log_time = datetime.datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")
	print "log time : " + log_time + "-----> cron job executed !!"
	
	codes = ['EUR', 'GBP', 'CNY', 'INR', 'AUD', 'CAD', 'AED', 'JPY', 'HKD', 'KRW']
	today = datetime.datetime.now().strftime("%Y-%m-%d")
	
	for code in codes:
		ex_data_quandl = getExchangeRate(code, today)[0]
		# print ex_data_quandl

		try:
			exchange_model = Exchange.objects.get(nation_code=code)
			print "model exists"
			print exchange_model.nation_code
			exData = json.loads(exchange_model.exData)
			exData.append(ex_data_quandl)

			exchange_model.exData = json.dumps(exData)
			exchange_model.save(update_fields=['exData'])
			print "update completed !!"

		except:
			print "model does not exist"

	

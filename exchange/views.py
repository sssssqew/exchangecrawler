# -*- coding: utf-8 -*- 
from django.shortcuts import render
from django.http import HttpResponse,  HttpResponseRedirect
from dateutil.relativedelta import relativedelta
import datetime
import urllib2
import json
import timeit
import numpy as np 
import quandl
import csv
# Create your views here.
from .models import Exchange
from quandl.errors.quandl_error import NotFoundError 

#set api key
quandl.ApiConfig.api_key = 'QWTqFXgs58dsasdnEqE7' #my account

# 데이터 수집기간 설정 
TERM = 5

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
	# column_names = exchangeRate_json['dataset']['column_names']
	# currency_id = exchangeRate_json['dataset']['dataset_code'][3:]
	return exchangeRates


# 검색할 기간의 날짜 생성  
def getStartDate(term):
	start_date = datetime.datetime.now() - relativedelta(years=term)
	return start_date

# 공백 제거 
def delete_spaces(words):
	w_list = []
	words = words.split(',')
	for word in words:
		w_list.append(word.strip())
	return w_list

# 검색할 기간의 날짜 생성  
def createDaysForYear(term):
	start_date = datetime.datetime.now() - relativedelta(years=term)
	end_date = datetime.datetime.now() + datetime.timedelta(days=1)
	
	days = []
	d = start_date
	while(d.year != end_date.year or d.month != end_date.month or d.day != end_date.day):
		days.append(d)
		d = d + datetime.timedelta(days=1)

	return days


def createDaysForWantedTerm(s_date, e_date):
	# start_date = datetime.datetime.now() - relativedelta(years=term)
	# end_date = datetime.datetime.now() + datetime.timedelta(days=1)
	
	days = []
	d = s_date
	while(d.year != e_date.year or d.month != e_date.month or d.day != e_date.day):
		days.append(d.strftime('%Y-%m-%d'))
		d = d + datetime.timedelta(days=1)

	return days


# 환율정보 디스플레이 
def index(request):
	print "--------------------------------------"
	print "rendering start..."

	isExist = False
	is_saved_alarm = 0

	selected_exchanges = []
	context = {}

	# DB 저장 체크 
	if request.GET.get('is_saved'):
		is_saved_alarm = int(request.GET.get('is_saved'))

	try: 
		selected_exchanges = delete_spaces(request.POST['selected_exchanges'])
		print selected_exchanges
	except:
		print "model successfully created !!"

	if selected_exchanges:
		not_exist_codes = []
		# day_list = []

		try:
			start_date_search = datetime.datetime.strptime(request.POST['start_date_search'], "%Y-%m-%d")
		except:
			start_date_search = datetime.datetime.strptime('2012-03-02', "%Y-%m-%d")
		try:
			end_date_search = datetime.datetime.strptime(request.POST['end_date_search'], "%Y-%m-%d")
		except:
			end_date_search = datetime.datetime.now()
		

		# day_list = createDaysForWantedTerm(start_date_search, end_date_search)
		# day_list.insert(0, 'x')

		columns = []


		# DB 조회 
		for code in selected_exchanges:
			try:
				
				exchange_model = Exchange.objects.get(nation_code=code)
				if(exchange_model):
					print "model exist in DB"
					print exchange_model.nation_code
				
				exData = json.loads(exchange_model.exData)
				np_exData = np.array(exData) # list to np array
				x = np_exData[:, 0] # np array
				y = np_exData[:, 1] # np array
				x_map = np.array(map(lambda p: datetime.datetime.strptime(p, "%Y-%m-%d"), x)) # np array

				condition = np.logical_and(x_map >=  start_date_search, x_map <= end_date_search)
				date = x[np.where(condition)].tolist()
				data = y[np.where(condition)].tolist()

				# print type(date)
				date.insert(0, 'x')
				data.insert(0, code)

				columns.append(data) 
				columns.insert(0, date)
		
			except:
				print "model doesn't exist in DB"
				not_exist_codes.append(code)


		# DB 존재하는 경우 
		if len(columns) > 1:
			isExist = True
			context = {"columns":json.dumps(columns), "not_codes":not_exist_codes, "isExistData":isExist}

			# file_name = 'quandl_web_exchangeRate.csv'

			# # 메이저 통화 배열 생성 
			# ex_ids = ['EUR', 'GBP', 'CNY', 'INR', 'AUD', 'CAD', 'AED', 'JPY', 'HKD', 'KRW']

			# # CSV 저장 
			# with open(file_name, 'w') as f:
			# 	writer = csv.writer(f, csv.excel)
			# 	for column in columns:
			# 		writer.writerow(column)


		else:
			context = {"not_codes":not_exist_codes, "isExistData":isExist}
	else:
		# print "sel is not !!"
		context = {"is_saved_alarm":is_saved_alarm, "isExistData":isExist}

	return render(request, 'exchange/search.html', context)



# 환율정보 DB 저장 
def store(request):
	is_saved = 0
	start_time = timeit.default_timer()
	exchanges = request.POST['exchanges']
	
	# 수집할 환율코드 및 날짜 배열 만들기 
	codes = delete_spaces(exchanges)
	start_date = getStartDate(TERM)

	# print codes
	# print days

	for code in codes:
		try:
			exchange_model = Exchange.objects.get(nation_code=code)
			print ("\n" + code + '  is already exists in database !!')

		except:
			ex_data = getExchangeRate(code, start_date.strftime("%Y-%m-%d"))
			exchange_model = Exchange(nation_code=code, exData=json.dumps(ex_data))
			exchange_model.publish()
			exchange_model.save() 
			print ("\n" + code + '  just saved in database !!')
			is_saved = 1
	

	# 실행시간 표시 
	elapsed = timeit.default_timer() - start_time
	print "------------------------------------------------------------------"
	print "실행시간(s): " + str(round(elapsed , 3)) + ' s'
	print "실행시간(min) : " + str(round(elapsed / 60 , 3)) + ' min'

	return HttpResponseRedirect("/"+"?is_saved="+str(is_saved))

def csvWriter(request):
	today = datetime.datetime.now().strftime("%Y-%m-%d")
	# Create the HttpResponse object with the appropriate CSV header.
	response = HttpResponse(content_type='text/csv')
	filename = "exchangeRate_" + today+".csv"
	response['Content-Disposition'] = 'attachment; filename=' + filename
	writer = csv.writer(response)

	try: 
		selected_exchanges = delete_spaces(request.POST['selected_exchanges'])
		print selected_exchanges
	except:
		print "you haven't enter exchange rate code !!"


	if selected_exchanges:
		not_exist_codes = []
		try:
			start_date_search = datetime.datetime.strptime(request.POST['start_date_search'], "%Y-%m-%d")
		except:
			start_date_search = datetime.datetime.strptime('2012-03-02', "%Y-%m-%d")
		try:
			end_date_search = datetime.datetime.strptime(request.POST['end_date_search'], "%Y-%m-%d")
		except:
			end_date_search = datetime.datetime.now()


		# DB 조회 
		for code in selected_exchanges:
			try:
				
				exchange_model = Exchange.objects.get(nation_code=code)
				if(exchange_model):
					print "model exist in DB"
					print exchange_model.nation_code
				
				exData = json.loads(exchange_model.exData)
				np_exData = np.array(exData) # list to np array
				x = np_exData[:, 0] # np array
				y = np_exData[:, 1] # np array
				x_map = np.array(map(lambda p: datetime.datetime.strptime(p, "%Y-%m-%d"), x)) # np array

				condition = np.logical_and(x_map >=  start_date_search, x_map <= end_date_search)
				date = x[np.where(condition)].tolist()
				data = y[np.where(condition)].tolist()

				# print type(date[3])

				for i in range(len(date)):
					writer.writerow([exchange_model.nation_code.encode('euc-kr'), date[i].encode('euc-kr'), data[i].encode('euc-kr'), data[i].encode('euc-kr'), data[i].encode('euc-kr'), data[i].encode('euc-kr')])

			except:
				print "model doesn't exist in DB"
				not_exist_codes.append(code)

	return response
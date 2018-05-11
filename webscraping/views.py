from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from collections import Counter
from operator import itemgetter
import time
import re
import requests
from celery.decorators import task
from celeryTask import Task
import json

prevTitle0 = ''
prevTitle1 = ''

currTask = None

def index(request=None, arguments={}):
	result = None
	global currTask
	if not arguments:
		title0 = request.GET['title0']
		selection0 = request.GET['selection0']
		title1 = request.GET['title1']
		selection1 = request.GET['selection1']
		if currTask != None:
			currTask.revoke()
			currTask = None
		currTask = getOptionList.delay(title0, title1, selection0, selection1)
		arguments = {'title0Val' : title0, 'title1Val' : title1, 'selection0Val' : selection0, 'selection1Val' : selection1, 'titleOptions0' : [], 'titleOptions1' : []}
	response = render(request, 'index.html', arguments)
	result_output = currTask.wait(timeout=None, interval=0.5)
	response = render(request, 'index.html', result_output)
	return response

@task(name="getOptionList")
def getOptionList(title0='', title1='', selection0='', selection1=''):
	patternList = re.compile('<h3 class="findSectionHeader"><a name="tt"><\/a>Titles<\/h3>\s*<table class="findList">\s*(.*)<\/table>')
	patternTitles = re.compile('<tr class="findResult (?:odd|even)?"> <td class="primary_photo"> <a href="\/title\/.*\/\?ref_=fn_al_tt_.*" ><img src=".*" \/><\/a> <\/td> <td class="result_text"> <a href="\/title\/.*\/\?ref_=fn_al_tt_.*" >(.*<\/a> \(.*\)(?: \(.*\))?) (?:.*)?<\/td>')
	url = ""
	response = None
	source = None
	optionList = []
	titleOptions0 = []
	if title0 != "":
		url = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + title0.replace(' ','+').split('(')[0] + "&s=all"
		response = requests.get(url, headers = {'Accept-Encoding' : 'identity'})
		source = response.text
		optionList = patternList.findall(source)[0].split("</tr>")
		optionList = optionList[:-1]
		for option in optionList:
			addOption = patternTitles.findall(option)[0].replace('</a>','')
			if addOption != selection0:
				titleOptions0.append({'title' : addOption, 'checked' : ''})
	if selection0 != '':
		titleOptions0.append({'title' : selection0, 'checked' : 'checked'})
	titleOptions1 = []
	if title1 != "":
		url = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + title1.replace(' ','+').split('(')[0] + "&s=all"
		response = requests.get(url, headers = {'Accept-Encoding' : 'identity'})
		source = response.text
		optionList = patternList.findall(source)[0].split("</tr>")
		optionList = optionList[:-1]
		for option in optionList:
			addOption = patternTitles.findall(option)[0].replace('</a>','')
			if addOption != selection1:
				titleOptions1.append({'title' : addOption, 'checked' : ''})
	if selection1 != '':
		titleOptions1.append({'title' : selection1, 'checked' : 'checked'})
	arguments = {'title0Val' : title0, 'title1Val' : title1, 'selection0Val' : selection0, 'selection1Val' : selection1, 'titleOptions0' : titleOptions0, 'titleOptions1' : titleOptions1}
	return arguments
	
def getWebscrapingTask(request, taskId):
	task = Task(taskId)
	return JsonResponse(task.getInfo())

def webscraping(request):
	title0 = request.GET['selection0']
	title1 = request.GET['selection1']
	if title0 == '' or title1 == '':
		return index(request=request)
	#get titles
	result = None
	cast = []
	searchTerm = title0.replace(' ','+').split('(')[0] + title0.replace(' ','+').split('(')[1]
	#get code (like tt1234567) to use in other urls and type (like movie or TV show)
	patternCode = re.compile('<td class="result_text">\s*<a href="\/title\/(.*)\/\?ref.=.........."\s*>.*<\/a>')
	url0 = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + searchTerm + "&s=all"
	response = requests.get(url0, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	code0 = patternCode.findall(source)[0].split("/")[0]
	url0 = "http://www.imdb.com/title/" + code0 + "/?ref_=nv_sr_1"
	response = requests.get(url0, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	url0 = "http://www.imdb.com/title/" + code0 +"/fullcredits?ref_=tt_cl_sm#cast"
	searchTerm = title1.replace(' ','+').split('(')[0] + title1.replace(' ','+').split('(')[1]
	url1 = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + searchTerm + "&s=all"
	response = requests.get(url1, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	code1 = patternCode.findall(source)[0].split("/")[0]
	url1 = "http://www.imdb.com/title/" + code1 + "/?ref_=nv_sr_1"
	response = requests.get(url1, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	url1 = "http://www.imdb.com/title/" + code1 +"/fullcredits?ref_=tt_cl_sm#cast"
	#get actors and characters
	patternActor = re.compile('<tr class="(?:odd|even)?">\s*<td class="primary_photo">\s<a href="\/name\/.*\/\?ref.=.*"\s><img height="44" width="32" alt="(.*?)" title')
	patternCharacter = re.compile('<td class=\"character\">\s*(?:&nbsp;)?(?:<a href=\".*\" >)?(.*)(?:<\/a>)?')
	response = requests.get(url0, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	matchesActors0 = patternActor.findall(source)
	matchesCharacters0 = patternCharacter.findall(source)
	response = requests.get(url1, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	matchesActors1 = patternActor.findall(source)
	matchesCharacters1 = patternCharacter.findall(source)
	#find actors that played in both and the characters they played
	cast = []
	for i in range(0, len(matchesActors0)):
		for j in range(0, len(matchesActors1)):
			if matchesActors0[i] == matchesActors1[j]:
				print(i)
				matchesCharacters0[i] = matchesCharacters0[i].replace('</a>', '')
				matchesCharacters1[j] = matchesCharacters1[j].replace('</a>', '')
				cast.append({'actor' : matchesActors0[i], 'character0' : matchesCharacters0[i], 'character1' : matchesCharacters1[j]})
	taskId = getRecommendedList.delay(title0, title1).task_id
	arguments = {'taskId' : taskId, 'title0' : title0.split('(')[0], 'title1' : title1.split('(')[0], 'cast' : cast}
	return render(request, 'webscraping.html', context=arguments)
	
@task(name="getRecommendedList")
def getRecommendedList(title0='', title1=''):
	#get recommended
	patternCode = re.compile('<td class="result_text">\s*<a href="\/title\/(.*)\/\?ref.=.........."\s*>.*<\/a>')
	patternType = re.compile('\(....\) \((.*)\)')
	patternGenre = re.compile('<a href="\/genre\/.*\?ref_=.*"\s*><span class="itemprop" itemprop="genre">(.*)<\/span><\/a>');
	searchTerm = title0.replace(' ','+').split('(')[0] + title0.replace(' ','+').split('(')[1]
	url0 = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + searchTerm + "&s=all"
	response = requests.get(url0, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	code0 = patternCode.findall(source)[0].split("/")[0]
	type0 = ''.join(x.capitalize() or '_' for x in patternType.findall(source)[0].split(")")[0].replace(' ','_').split('_'))
	type0 = type0[0].lower() + type0[1:]
	url0 = "http://www.imdb.com/title/" + code0 + "/?ref_=nv_sr_1"
	response = requests.get(url0, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	matchesGenres0 = patternGenre.findall(source)
	url0 = "http://www.imdb.com/title/" + code0 +"/fullcredits?ref_=tt_cl_sm#cast"
	searchTerm = title1.replace(' ','+').split('(')[0] + title1.replace(' ','+').split('(')[1]
	url1 = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + searchTerm + "&s=all"
	response = requests.get(url1, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	code1 = patternCode.findall(source)[0].split("/")[0]
	type1 = ''.join(x.capitalize() or '_' for x in patternType.findall(source)[0].split(")")[0].replace(' ','_').split('_'))
	type1 = type1[0].lower() + type1[1:]
	url1 = "http://www.imdb.com/title/" + code1 + "/?ref_=nv_sr_1"
	response = requests.get(url1, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	matchesGenres1 = patternGenre.findall(source)
	url1 = "http://www.imdb.com/title/" + code1 +"/fullcredits?ref_=tt_cl_sm#cast"
	url0 = "http://www.imdb.com/title/" + code0 +"/keywords?ref_=tt_stry_kw"
	url1 = "http://www.imdb.com/title/" + code1 +"/keywords?ref_=tt_stry_kw"
	patternKeywords = re.compile('<td class="soda sodavote" data-item-votes=".*" data-item-keyword="(.*)">')
	response = requests.get(url0, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	matchesKeywords0 = patternKeywords.findall(source)
	response = requests.get(url1, headers = {'Accept-Encoding' : 'identity'})
	source = response.text
	matchesKeywords1 = patternKeywords.findall(source)
	keywords = []
	for keyword0 in matchesKeywords0:
		for keyword1 in matchesKeywords1:
			if keyword0 == keyword1:
				keywords.append(keyword0)
	genres = []
	for genre0 in matchesGenres0:
		for genre1 in matchesGenres1:
			if genre0 == genre1:
				genres.append(genre0)
	patternRecommended = re.compile('<a href="\/title\/.*\/\?ref_=kw_li_tt"\s*>(.*)<\/a>')
	patternRatings = re.compile('<span class="genre">\s*.*<\/span>\s*.*\s*.*\s*<\/p>\s*(<div class="ratings-bar">\s*<div class="inline-block ratings-imdb-rating" name="ir" data-value=".*">)?')
	matchesRecommended = []
	matchesRatings = []
	for keyword in keywords:
		if type0 == type1:
			url = "http://www.imdb.com/search/keyword?keywords=" + keyword + "&sort=moviemeter,asc&mode=detail&page=1&title_type=" + type0 + "&ref_=kw_ref_typ"
		else:
			url = "http://www.imdb.com/search/keyword?keywords=" + keyword + "&sort=moviemeter,asc&mode=detail&page=1&ref_=kw_ref_typ"
		response = requests.get(url, headers = {'Accept-Encoding' : 'identity'})
		source = response.text
		matchesRecommended += patternRecommended.findall(source)
		matchesRatings += patternRatings.findall(source)
	for genre in genres:
		if type0 == type1:
			url = "http://www.imdb.com/search/keyword?sort=moviemeter,asc&mode=detail&page=1&title_type=" + type0 + "&genres=" + genre + "&ref_=kw_ref_typ"
		else:
			url = "http://www.imdb.com/search/keyword?sort=moviemeter,asc&mode=detail&page=1&genres=" + genre + "&ref_=kw_ref_gnr"
		response = requests.get(url, headers = {'Accept-Encoding' : 'identity'})
		source = response.text
		matchesRecommended += patternRecommended.findall(source)
		matchesRatings += patternRatings.findall(source)
	for i in range(0, len(matchesRatings)):
		if matchesRatings[i] != "":
			parts = matchesRatings[i].split('"')
			matchesRatings[i] = parts[len(parts)-2]
			if len(matchesRatings[i]) == 1:
				matchesRatings[i] += ".0"
		else:
			matchesRatings[i] = "0.0"
	counter = Counter(matchesRecommended).items()
	recommended = [[], []]
	for i in range(0, len(counter)):
		if title0.split('(')[0][:-1] != counter[i][0] and title1.split('(')[0][:-1] != counter[i][0] and counter[i][1] > 2:
				recommended[0].append(matchesRecommended[matchesRecommended.index(counter[i][0])])
				recommended[1].append(matchesRatings[matchesRecommended.index(counter[i][0])])
	if len(recommended[0]) <= 10:
		recommended = [[], []]
		for i in range(0, len(counter)):
			if title0.split('(')[0][:-1] != counter[i][0] and title1.split('(')[0][:-1] != counter[i][0] and counter[i][1] > 1:
				recommended[0].append(matchesRecommended[matchesRecommended.index(counter[i][0])])
				recommended[1].append(matchesRatings[matchesRecommended.index(counter[i][0])])
	if len(recommended[0]) <= 5:
		recommended = [[], []]
		for i in range(0, len(counter)):
			if title0.split('(')[0][:-1] != counter[i][0] and title1.split('(')[0][:-1] != counter[i][0]:
				recommended[0].append(matchesRecommended[matchesRecommended.index(counter[i][0])])
				recommended[1].append(matchesRatings[matchesRecommended.index(counter[i][0])])
	recommended = zip(*recommended)
	recommended.sort(reverse = True, key = lambda x: x[1])
	recommended = zip(*recommended)
	return recommended[0]

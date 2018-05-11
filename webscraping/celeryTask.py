from celery.result import AsyncResult
		
class Task(object):
	def __init__(self, id):
		self.id = id
		self.result = AsyncResult(id)
		
	def getInfo(self):
		if self.result.ready():
			recommendations = ""
			i = 0
			for movie in self.result.result:
				recommendations += movie
				recommendations += "|"
				i += 1
				if i > 20:
					break
			recommendations = recommendations[:-1]
			return {
				'complete': 'True',
				'recommendations': recommendations
			}
		return {
			'complete': 'False'
		}

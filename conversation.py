import random
import re

class Conversation(object):
	def __init__(self):
		self.responses = {
			'english': {
				'greeting': 
					"If this is an emergency please call 999. Hello, this is Dr. Fatma. I am an automated " +
					"service, and I would like to provide assistance with your medical symptoms. How can I " +
					"help you?",
				'symptom_check': [
					"I am sorry to hear that. Are you also experiencing {}?", 
					"I understand. Are you feeling any {}?",
					"Have you noticed any {}?",
				],
				'symptoms_length': "Hmmm. How long have you been experiencing {}?",
				'disease_confirm': 
					"If I understand correctly, you have been feeling {} since {}. It sounds like you may" +
					"have food poisoning. Please avoid caffeine and make sure to remain properly hydrated. " +
					"If your symptoms become any worse, please visit an emergency room.",
			},
			'arabic': {
				'greeting': (
"""إذا كان هذا هو حالة الطوارئ يرجى الاتصال 999. مرحبا، وهذا هو الدكتور فاطمة. أنا خدمة الآلي،
وأود أن أقدم المساعدة مع الأعراض الطبية الخاصة بك. كيف بإمكاني مساعدتك؟"""
				),
			},
		}
		self.disease_symptoms = set(['nausea', 'headache', 'diarrhea', 'fever', 'loss of appetite'])
		self.keywords = self.disease_symptoms.copy()
		self.keywords.update(['nauseous', 'yes', 'yeah', 'not', 'no'])
		self.lemmatize = {
			'nauseous': 'nausea',
			'yeah': 'yes',
			'not': 'no',
		}
		self.symptoms_to_check = self.disease_symptoms.copy()
		self.experienced_symptoms = set()
		self.last_asked_symptom = ''
		self.time_since_symptoms = 'yesterday'
		self.stage = 'greeting'
		self.language = 'english'

	def respond(self, message):
		keywords = self.getKeywords(message)
		if self.stage == 'greeting':
			response = []
			for language in ('english', 'arabic'):
				response.append((self.responses[language]['greeting'], language))
			self.stage = 'symptom_check'
			return response

		elif self.stage == 'symptom_check':
			new_symptoms = set()
			if self.last_asked_symptom != '' and 'yes' in keywords:
				new_symptoms.add(self.last_asked_symptom)
			for symptom in self.symptoms_to_check:
				if symptom in keywords:
					new_symptoms.add(symptom)
			self.symptoms_to_check -= new_symptoms
			self.experienced_symptoms.update(new_symptoms)
			if len(self.symptoms_to_check) > 0:
				next_symptom = random.choice(list(self.symptoms_to_check))
				response = random.choice(self.responses[self.language]['symptom_check'])
				response = response.format(next_symptom)
				self.last_asked_symptom = next_symptom
				self.symptoms_to_check.remove(next_symptom)
			elif self.experienced_symptoms == self.disease_symptoms:
				response = self.responses[self.language]['symptoms_length']
				response = response.format(random.choice(list(new_symptoms)))
				self.stage = 'disease_confirm'

		elif self.stage == 'disease_confirm':
			response = self.responses[self.language]['disease_confirm']
			experienced_symptoms = list(self.experienced_symptoms)
			symptoms = "{}, and {}".format(', '.join(experienced_symptoms[:-1]), experienced_symptoms[-1])
			response = response.format(symptoms, self.time_since_symptoms)

		return [(response, self.language)]

	def getKeywords(self, message):
		keywords = set()
		for word in re.findall('\w+', message, re.I):
			word = word.lower()
			if word in self.keywords:
				word = self.lemmatize.get(word, word)
				keywords.add(word)
		return keywords

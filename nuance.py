import requests
import secrets
import uuid

# Testing with audio sample
audio_data = {}
with open('english_audio_sample.wav', 'rb') as audio_file:
  audio_data['english'] = audio_file.read()
with open('arabic_audio_sample.wav', 'rb') as audio_file:
  audio_data['arabic'] = audio_file.read()

language_codes = {
  'arabic': 'ara-XWW',
  'english': 'eng-USA',
}
asr_url = "https://dictation.nuancemobility.net:443/NMDPAsrCmdServlet/dictation" 
userId = uuid.uuid4()
params = {
  'arabic': {
    'appId': secrets.appId_arabic,
    'appKey': secrets.appKey_arabic,
    'id': userId,
  },
  'english': {
    'appId': secrets.appId_english,
    'appKey': secrets.appKey_english,
    'id': userId,
  },
}
headers = {
  'Content-Type': 'audio/x-wav;codec=pcm;bit=16;rate=16000',
  # 'Content-Length': len(audio_data),
  'Accept': 'text/plain;charset=utf-8',
  'Accept-Topic': 'Dictation',
  'X-Dictation-NBestListSize': '1',
}
for language in ('english', 'arabic'):
  headers.update({
    'Accept-Language': language_codes[language],
    'Content-Length': len(audio_data[language]),
  })
  r = requests.post(asr_url, params=params[language], headers=headers, data=audio_data[language])
  print(r.text)

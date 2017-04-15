import requests
import secrets
import uuid

asr_url = "https://dictation.nuancemobility.net:443/NMDPAsrCmdServlet/dictation" 
tts_url = "https://tts.nuancemobility.net:443/NMDPTTSCmdServlet/tts"
language_codes = {
  'arabic': 'ara-XWW',
  'english': 'eng-USA',
}
params = {
  'arabic': {
    'appId': secrets.appId_arabic,
    'appKey': secrets.appKey_arabic,
    'id': uuid.uuid4(),
    'voice': 'Laila',
  },
  'english': {
    'appId': secrets.appId_english,
    'appKey': secrets.appKey_english,
    'id': uuid.uuid4(),
    'voice': 'Zoe',
  },
}

def speech_to_text(audio):
  headers = {
    'Content-Type': 'audio/x-wav;codec=pcm;bit=16;rate=16000',
    'Accept': 'text/plain;charset=utf-8',
    'Accept-Topic': 'Dictation',
    'X-Dictation-NBestListSize': '1',
  }
  results = []
  for language in ('english', 'arabic'):
    headers.update({
      'Accept-Language': language_codes[language],
      'Content-Length': len(audio),
    })
    r = requests.post(asr_url, params=params[language], headers=headers, data=audio)
    results.append(r.text)
  return results

def text_to_speech(text, language):
  headers = {
    'Content-Type': 'text/plain;charset=utf-8',
    'Accept': 'audio/x-wav;codec=pcm;bit=16;rate=16000',
  }
  r = requests.post(tts_url, params=params[language], headers=headers, data=text)
  return r.content

if __name__ == '__main__':
  with open('english_audio_sample.wav', 'rb') as file:
    audio = file.read()
    print(speech_to_text(audio))
  text = "Hello, my name is Dr. Fatimah."
  with open('english_speech_synthesis.wav', 'wb') as file:
    file.write(text_to_speech(text, 'english'))

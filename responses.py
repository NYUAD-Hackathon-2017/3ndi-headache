import main

import numpy as np
import soundfile as sf


responses = [
 "If this is an emergency please call 9 9 9. Hello, this is Dr. Fatima. I am here to assist you with your medical symptoms. Are you calling for yourself or someone else?",
 "What is your name?",
 "How may I help you Khaled?",
 "I am sorry to hear that. Are you also experiencing diarrhea?",
 "I understand. How long have you been experiencing diarrhea?",
 "Okay, so you've been having headaches, a fever, nausea, and diarrhea. Are there any other symptoms that you are feeling?",
 "You should probably meet a doctor about this. If you would like, I can book you an appointment with the abdominal pain specialist at Cleveland Clinic.",
 "There is an appointment available on Friday, 4 P M. Is that okay with you?",
 "Okay, I have booked your appointment. I hope you feel better soon. Goodbye.",
]


for i, resp in enumerate(responses):
  sound = main.text_to_speech(resp, language='english')
  bits = np.fromstring(sound, dtype='<i2')
  sf.write('static/{}.wav'.format(i), bits * 1. / 32000, 16000)

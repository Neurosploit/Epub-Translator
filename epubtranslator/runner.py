__author__ = 'sha256'

from epubtranslator.bookprocessor import ConversionEngine, BookProcessor
import requests, uuid, time

class ProgressCallback(object):

    def __init__(self):
        self._total = 0
        self._progress = 0

    def update_state(self, event, val=None):

        if event == "total":
            self._total = val
        elif event == "start":
            self._progress += 4.0/self._total
        elif event == "finish":
            self._progress += 94.0/self._total
        elif event == "complete":
            self._progress = 100


class SimpleConversionEngine(ConversionEngine):

    def __init__(self):
        self.totaltextsize = 0
        self.currentMinuteCharactersConverted = 0
        self.sleepCount = 0
        self.cognitiveServiceUrl = 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken'
        self.translateUrl = 'https://api.cognitive.microsofttranslator.com/'
        self.maxTextLength = 5000  # limit on max characters at same time from single api call.
		self.rateLimitLength = 33000 # when rate limit kicks in.
        # create a file yourself with the azure congnitive api key in it on a single line.
        with open('azurecognitiveapi.key', 'r') as myfile:
            self.subscriptionKey = myfile.read()
        self.token = self.getAccessToken()

    def convert(self, text, fromlang, tolang):
        # conversion logic here
        # to not hit rate limit sleep 60 seconds before continuing
         print('trying to convert '+ text)
         if((self.currentMinuteCharactersConverted + len(text)) >= self.rateLimitLength):
             print('sleeping')
             time.sleep(60)
             self.sleepCount +=1
             self.currentMinuteCharactersConverted = 0

         # token is valid for 10 minutes, request one every 5 sleep cycles(5* 60 seconds + request times in between) to be on the safe side.
         if(self.sleepCount == 5):
             self.token = self.getAccessToken()
             self.sleepCount = 0

         self.currentMinuteCharactersConverted += len(text)
         self.totaltextsize += len(text)

         if(len(text) >= self.maxTextLength):
             print('detected splits')
             translatedText = ''
             splits = self.splitText(text)
             for split in splits:
                 translatedSplit = self.convertSplit(split, fromlang, tolang)
                 translatedText = self.appendSplit(translatedText, translatedSplit)
             return translatedText
         else:
             print('detected normal translation')
             translation = self.getTranslationFromAzure(text, fromlang, tolang)
             return translation

    def convertSplit(self, split, fromlang, tolang):
        return self.getTranslationFromAzure(split, fromlang, tolang)

    def splitText(self, text):
        retsplits = []
        curMerge = ''
        splits = str.split(text, '.')

        # assumes that the split length is smaller than self.maxTextLength.
        for split in splits:
            dottedsplit = split + '.'
            if(len(curMerge + dottedsplit) >= self.maxTextLength):
                retsplits.append((curMerge))
                curMerge = dottedsplit
            else:
                curMerge += dottedsplit
        retsplits.append((curMerge))
        return retsplits

    def appendSplit(self, translatedText, translatedSplit):
        return translatedText + translatedSplit

    def getTranslationFromAzure(self, text, fromlang, tolang):
        print('request start')
        path = '/translate?api-version=3.0'
        params = '&from=' + fromlang + '&to=' + tolang
        constructed_url = self.translateUrl + path + params

        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        body = [{
            'text': text
        }]
        request = requests.post(constructed_url, headers=headers, json=body)
        response = request.json()
        print('request done')
        return response[0]["translations"][0]["text"]

    def getAccessToken(self):
        print('requesting new token ')
        requestheader = {'Ocp-Apim-Subscription-Key': self.subscriptionKey}
        responseresult = requests.post(self.cognitiveServiceUrl, headers=requestheader)
        token = responseresult.text
        return token

if __name__ == "__main__":
    e = SimpleConversionEngine()
    u = BookProcessor(e, progress_callback=ProgressCallback())
    u.set_file("../EpubIn/input.epub", "../EpubOut/output.epub", "it", "en")
    u.convert()
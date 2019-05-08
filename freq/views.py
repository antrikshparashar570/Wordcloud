import tornado.web
import mysql.connector
import requests
import json
from bs4 import BeautifulSoup
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64
import hashlib, uuid
from Crypto.Cipher import AES


class render(tornado.web.RequestHandler):
    def get(self):
        self.render("search.html")

class freqwords(tornado.web.RequestHandler):
    def get(self):
        Url = self.get_argument("url")
        resp = requests.get(url = 'http://' + Url)
        soup=BeautifulSoup(resp.text, 'html.parser')
        text = soup.find('title')
        text = text.renderContents()
        


        url = 'https://api.wit.ai/message?q=' + text.decode()
        auth = 'Bearer ' + '4YQCST5N7P7JF7QA4Z4EDSPC6BOU4U2J'
        headers = {'Authorization': auth}
        res = requests.post(url=url, headers=headers)
        res = res.json()
        
        
        
        
        salt = uuid.uuid4().hex
        hashed_url = hashlib.sha512(Url.encode('utf-8') + salt.encode('utf-8')).hexdigest() 

        conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', passwd='justdial', db='frewords')
        cur = conn.cursor()


        cur.execute("TRUNCATE TABLE sentiment")
        cur.execute("INSERT INTO sentiment (url,sentiment,hashed_url) VALUES ('%s','%s','%s')" % (Url,res['entities']['sentiment'][0]['value'],hashed_url))


        headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
        }
        Params = {'task': "wordfreqUrl",'url':Url,'options':"ignoreStopWords"}
        r = requests.post(url = "https://www.wordclouds.com/ajax.php", headers=headers, data = Params)

        data = r.json()
        data['data']['list'] = data['data']['list'][:10]
        #self.write(data)
        
        comment_words = ' '
        stopwords = set(STOPWORDS) 
	  
        for val in data['data']['list']: 
            val = val[0]
            #self.write(val)
            tokens = val.split()
            for i in range(len(tokens)): 
                tokens[i] = tokens[i].lower() 
            for words in tokens: 
                comment_words = comment_words + words + ' '
									    
        wordcloud = WordCloud(width = 800, height = 800, background_color ='white', stopwords = stopwords, min_font_size = 10).generate(comment_words) 
														                                
        fig = plt.figure(figsize = (8, 8), facecolor = None)  
        plt.imshow(wordcloud) 
        plt.axis("off") 
        plt.tight_layout(pad = 0)
        figdata = BytesIO()
        fig.savefig(figdata, format='png')
        self.set_header('Content-Type', 'text/html')
        self.write('<html><body><img src="data:image/png;base64,%s"/></body></html>' % base64.b64encode(figdata.getvalue()).decode('utf-8')) 

       
       
       
       
        cur.execute("TRUNCATE TABLE words")
        
        for a in data['data']['list']:
            key1 = 'This is a key123'
            key2 = 'This is an IV456' 
            obj = AES.new(key1.encode('ascii','ignore'), AES.MODE_CFB, key2.encode('ascii','ignore'))
            ciphertext = obj.encrypt(a[0].encode('ascii','ignore'))
            ciphertext = base64.b64encode(ciphertext).decode()
	    
	    
            salt = uuid.uuid4().hex
            hashed_word = hashlib.sha512(a[0].encode('utf-8') + salt.encode('utf-8')).hexdigest() 
            
	     
            cur.execute("INSERT INTO words (frequency,hashed_word,encrypted_word) VALUES ('%d','%s','%s')" % (a[1],hashed_word,ciphertext))

        conn.commit()
        cur.close() 
        conn.close()

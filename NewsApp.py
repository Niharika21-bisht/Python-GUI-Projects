import io
import webbrowser
import requests
from tkinter import *
from urllib.request import urlopen
from PIL import ImageTk, Image

class NewsApp:

    def __init__(self):
        #fetch data
        self.data = requests.get('https://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey=6c37f3c4a1924405a23d9ea1f8102b3c').json()
       
        
        #Load GUI
        self.load_GUI()

        self.load_news_item(0)

        self.root.mainloop()

        


    def load_GUI(self):
        self.root = Tk()
        self.root.title('News App')
        self.root.geometry('350x600')
        self.root.resizable(0,0)
        self.root.configure(background='black')

    def clear(self):
        for i in self.root.pack_slaves():
            i.destroy()


    def load_news_item(self,index):

        #clear the screen for new news item
        self.clear()
        try:
            img_url = self.data['articles'][index]['urlToImage']
            raw_data = urlopen(img_url).read()
            img = Image.open(io.BytesIO(raw_data)).resize((350,250))
            self.photo = ImageTk.PhotoImage(img)
        except:
            img_url = 'https://www.shutterstock.com/image-vector/no-photo-blank-image-icon-loading-1955339317'
            raw_data = urlopen(img_url).read()
            img = Image.open(io.BytesIO(raw_data)).resize((350,250))
            self.photo = ImageTk.PhotoImage(img)


        img_label = Label(self.root,image=self.photo)
        img_label.pack()
        



        #load heading
        heading = Label(self.root,text=self.data['articles'][index]['title'],bg='black',fg='white',wraplength=350,justify='center')
        heading.pack(pady=(10,20))
        heading.config(font=('verdana',15))

        details = Label(self.root,text=self.data['articles'][index]['description'],bg='black',fg='white',wraplength=350,justify='center')
        details.pack(pady=(2,20))
        details.config(font=('verdana',12))

        frame = Frame(self.root,background='black')
        frame.pack(expand=True,fill=BOTH)

        if index != 0:
            prev = Button(frame,text='Prev',width=16,height=3,command=lambda: self.load_news_item(index-1))
            prev.pack(side=LEFT)

        read = Button(frame,text='Read More',width=16,height=3,command=lambda: self.open_link(self.data['articles'][index]['url']))
        read.pack(side=LEFT)

        if index != len(self.data['articles'])-1:
            next = Button(frame,text='Next',width=16,height=3,command=lambda: self.load_news_item(index+1))
            next.pack(side=LEFT)

    def open_link(self,url):
        webbrowser.open(url)


obj = NewsApp()
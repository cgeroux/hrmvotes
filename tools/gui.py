import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
import PySide6.QtGui as qtg
import sys
import subprocess as sp
import datetime as dt
import json
import urllib.parse as urlp
import copy
import re
import lxml.html
import requests
import time

backGroundStyle="background-color:#404040;"

'''
def downloadSubTitles(url,outFileName="temp"):
  cmd=["yt-dlp","--skip-download","--write-subs",
       "--sub-langs", "en","--write-auto-subs",
       "-o",outFileName,url]
  result=sp.run(cmd,capture_output=True)
  if result.returncode!=0:
    print("rc="+str(result.returncode))
    print("stdout="+str(result.stdout))
    print("stderr="+str(result.stderr))
'''
def getTitle(url):
  cmd=["yt-dlp","--skip-download","--get-title",url]
  result=sp.run(cmd,capture_output=True)
  if result.returncode!=0:
    print("rc="+str(result.returncode))
    print("stdout="+str(result.stdout))
    print("stderr="+str(result.stderr))
  title=str(result.stdout.strip())
  return title
def getVotetimes(url,fileName='temp.en.vtt',minSecondsBetweenVotes=30):
  file=open(fileName)
  ts=None
  te=None
  timeLastVote=None
  voteTimeUrls=[]
  for line in file:
    line=line.strip()
    if "-->" in line:
      #print("| \""+line+"\"")
      times=line.split(" --> ")
      #print("ts: "+str(times[0])+" te: "+str(times[1]))
      ts=times[0]
      te=times[1]
      
    else:
      
      voteInProgress=False
      if "[ Voting in Progress ]" in line:
        voteInProgress=True
      
      wordVoteMentioned=False
      if "vote" in line or "VOTE" in line or "Vote" in line:
        wordVoteMentioned=True
      
      recordedVote=False
      if "recorded vote" in line or "Recorded vote" in line or "RECORDED VOTE" in line:
        recordedVote=True
      
      if voteInProgress or wordVoteMentioned or recordedVote:
        
        ts=ts.split('.')[0]#NOTE: remove fractional seconds
        #print("ts="+str(ts))
        curTime=dt.datetime.strptime(ts,"%H:%M:%S")
        timeBetweenVote=False
        if timeLastVote!=None:
          timeDelta=curTime-timeLastVote
          if timeDelta.total_seconds()>minSecondsBetweenVotes:
            timeBetweenVote=True
        else:
          timeBetweenVote=True
          
        if timeBetweenVote:
          
          timeLastVote=curTime
          urlVote=url+"?t="+str(int(timeLastVote.hour*60*60+timeLastVote.minute*60+timeLastVote.second))
          addVoteTime=False
          if voteInProgress:
            print("vote in progress at "+str(ts)+" "+str(urlVote))
            addVoteTime=True
          else:
            if recordedVote:
              print("words \"recorded vote\" mentioned at "+str(ts)+" "+str(urlVote))
              addVoteTime=True
            else:
              if wordVoteMentioned:
                print("word \"vote\" mentioned at "+str(ts)+" "+str(urlVote))
                addVoteTime=True
          if addVoteTime:
            voteTimeUrls.append(urlVote)
  return voteTimeUrls
def getTotalSeconds(timeDict):
  timeSeconds=int(timeDict["h"]*60*60+timeDict["m"]*60+
    timeDict["s"])
  return timeSeconds
class MainWindow(qtw.QMainWindow):
  def __init__(self):
    super().__init__()
    
    self.loadDatabase()
    self.attemptToSetCurrentVideoFromDatabase()
    
    self.centralWidget=qtw.QStackedWidget()
    self.setCentralWidget(self.centralWidget)
    
    self.setWindowTitle("My App")
    self.statusBar=self.statusBar()
    
    self.createTaskToolBar()
    
    self.createAddVideoWidget()
    self.createAddVoteWidget()
    self.createNotificationWidget()
    
    if self.hasUnprocessedVideos():
      self.switchToAddVoteMode()
      self.showStatusMessage("Has videos to process")
    else:
      self.switchToAddVideoMode()
      self.showStatusMessage("No videos to process, try adding one")
  def showStatusMessage(self,message,timeout=0):
    self.statusBar.showMessage(message,timeout=timeout)
  def hasUnprocessedVideos(self):
    if self.currentVideo==None:
      self.attemptToSetCurrentVideoToAnUnprocessedVideo()
    return self.currentVideo!=None
  def createTaskToolBar(self):
    
    toolBar=qtw.QToolBar("Task bar")
    self.addToolBar(toolBar)
    
    buttonVideo=qtg.QAction("Add video",self)
    buttonVideo.setStatusTip("Add a link to a youtube video to process")
    buttonVideo.triggered.connect(self.addVideoTaskClicked)
    toolBar.addAction(buttonVideo)
    
    buttonVote=qtg.QAction("Add votes",self)
    buttonVote.setStatusTip("Add votes")
    buttonVote.triggered.connect(self.addVotesTaskClicked)
    toolBar.addAction(buttonVote)
  def switchToAddVoteMode(self):
    self.centralWidget.setCurrentWidget(self.addVotewidget)
    if self.currentVideo==None:
      self.attemptToSetCurrentVideoToAnUnprocessedVideo()
    
    self.ensureCurrentVideoHasVoteTimes()
    
    self.ensureCurrentTimeSet()
    self.updateAddVoteWidget()
  def checkLine(self,linePrev,lineCur,lineNext,ts,te,timeLastVote,voteTimes,
    voteTimesOrder):
    
    minSecondsBetweenVotes=self.database["minSecondsBetweenVoteEvents"]
    matchWords=self.database["matchWords"]
    
    if lineCur!="":
      lineCur=lineCur.strip()
      if "-->" in lineCur:
        times=lineCur.split(" --> ")
        ts=times[0]
        te=times[1]
      else:
        
        hadMatch=False
        wordMatched=None
        for word in matchWords:
          wordLower=word.lower()
          lineLower=lineCur.lower()
          if wordLower in lineLower:
            hadMatch=True
            wordMatched=word
            matchedLinePrev=re.sub(r"<.*?>","",linePrev)
            matchedLineCur=re.sub(r"<.*?>","",lineCur)
            matchedLineNext=re.sub(r"<.*?>","",lineNext)
        if hadMatch:
          
          ts=ts.split('.')[0]#NOTE: remove fractional seconds
          curTime=dt.datetime.strptime(ts,"%H:%M:%S")
          timeBetweenVote=False
          if timeLastVote!=None:
            timeDelta=curTime-timeLastVote
            if timeDelta.total_seconds()>minSecondsBetweenVotes:
              timeBetweenVote=True
          else:
            timeBetweenVote=True
            
          if timeBetweenVote:
            
            timeLastVote=curTime
            timeDict={"h":timeLastVote.hour,"m":timeLastVote.minute,
              "s":timeLastVote.second}
            timeSeconds=getTotalSeconds(timeDict)
            
            int(timeLastVote.hour*60*60+timeLastVote.minute*60+
              timeLastVote.second)
            voteTime={"time":timeDict,"wordMatched":wordMatched,
              "matchedLinePrev":matchedLinePrev,
              "matchedLineCur":matchedLineCur,
              "matchedLineNext":matchedLineNext}
            voteTimes[str(timeSeconds)]=voteTime
            voteTimesOrder.append(str(timeSeconds))
    return (ts,te,timeLastVote)
  def ensureCurrentVideoHasVoteTimes(self):
    
    self.ensureCurrentVideoHasSubtitles()
    self.showStatusMessage("Ensuring current video has vote times")
    url=self.currentVideo
    video=self.database["videos"][url]
    addVoteTimes=True
    if "voteTimes" in video.keys():
      voteTimes=video["voteTimes"]
      voteTimesOrder=video["voteTimesOrder"]
      if len(voteTimes)>0:
        addVoteTimes=False
    else:
      video["voteTimes"]={}
      video["voteTimesOrder"]=[]
      voteTimes=video["voteTimes"]
      voteTimesOrder=video["voteTimesOrder"]
    if addVoteTimes:
      file=open(video["subtitleFile"],'r')
      ts=None
      te=None
      timeLastVote=None
      linePrev=""
      lineCur=""
      lineNext=""
      for line in file:
        linePrev=lineCur
        lineCur=lineNext
        lineNext=line
        
        (ts,te,timeLastVote)=self.checkLine(linePrev,lineCur,lineNext,ts,te,
          timeLastVote,voteTimes,voteTimesOrder)
      
      linePrev=lineCur
      lineCur=lineNext
      lineNext=""
      self.checkLine(linePrev,lineCur,lineNext,ts,te,timeLastVote,voteTimes,
        voteTimesOrder)
  def getCurrentVideo(self):
    if self.currentVideo==None:
      #assert self.hasUnprocessedVideos()
      #videos=self.database["videos"]
      #self.currentVideo=videos.keys()[0]
      setVideo=self.attemptToSetCurrentVideoToAnUnprocessedVideo()
      assert setVideo
    return self.currentVideo
  def ensureCurrentTimeSet(self):
    if self.currentTime==None:
      assert self.currentVideo!=None
      video=self.database["videos"][self.currentVideo]
      assert "voteTimes" in video.keys()
      self.currentTime=video["voteTimesOrder"][0]
      self.database["currentTime"]=self.currentTime
  def attemptToSetCurrentVideoToAnUnprocessedVideo(self):
    currentVideoSet=False
    if "videos" in self.database.keys():
      if len(self.database["videos"])>0:
        for key in self.database["videos"].keys():
          video=self.database["videos"][key]
          if video["status"]=="unprocessed":
            self.currentVideo=key
            if "voteTimes" in video.keys():
              self.currentTime=video["voteTimesOrder"][0]
            else:
              self.currentTime=None
            
            self.database["currentTime"]=self.currentTime
            self.database["currentVideo"]=self.currentVideo
            currentVideoSet=True
    return currentVideoSet
  def attemptToSetCurrentVideoFromDatabase(self):
    currentVideoSet=False
    if "currentVideo" in self.database.keys():
      self.currentVideo=self.database["currentVideo"]
      currentVideoSet=True
      if "currentTime" in self.database.keys():
        self.currentTime=self.database["currentTime"]
      else:
        self.currentTime=None
    return currentVideoSet
  def ensureCurrentVideoHasSubtitles(self):
    if self.currentVideo!=None:
      self.showStatusMessage("Ensuring current video has subtitles")
      url=self.currentVideo
      video=self.database["videos"][url]
      outFileName="temp"
      if not("subtitleFile" in video.keys()):
        self.showStatusMessage("Download video subtitles")
        cmd=["yt-dlp","--skip-download","--write-subs",
            "--sub-langs", "en","--write-auto-subs",
            "-o",outFileName,url]
        result=sp.run(cmd,capture_output=True)
        if result.returncode!=0:
          print("rc="+str(result.returncode))
          print("stdout="+str(result.stdout))
          print("stderr="+str(result.stderr))
          raise Exception("Failed to download video subtitles")
        video["subtitleFile"]=outFileName+".en.vtt"
  def switchToAddVideoMode(self):
    self.centralWidget.setCurrentWidget(self.addVideowidget)
  def switchToNotificationMode(self,message):
    self.notificationWidget.setText(message)
    self.centralWidget.setCurrentWidget(self.notificationWidget)
  def createAddVideoWidget(self):
    topLayout=qtw.QVBoxLayout()
    self.addVideoText=qtw.QLineEdit()
    self.addVideoText.setStyleSheet(backGroundStyle)
    self.addVideoText.setPlaceholderText("Paste video link here")
    topLayout.addWidget(self.addVideoText)
    
    date=qtc.QDate.currentDate()
    
    dateLayout=qtw.QHBoxLayout()
    dateLabel=qtw.QLabel("Video date (M/D/Y):")
    dateLayout.addWidget(dateLabel)
    self.addVideoDate=qtw.QDateEdit(date)
    dateLayout.addWidget(self.addVideoDate)
    
    topLayout.addLayout(dateLayout)
    
    addVideoButton=qtw.QPushButton("Add video")
    addVideoButton.clicked.connect(self.addVideoButtonClicked)
    topLayout.addWidget(addVideoButton)
    
    self.addVideowidget=qtw.QWidget()
    self.addVideowidget.setLayout(topLayout)
    
    self.centralWidget.addWidget(self.addVideowidget)
  def createNotificationWidget(self):
    self.notificationWidget=qtw.QLabel()
    self.centralWidget.addWidget(self.notificationWidget)
  def createAddVoteWidget(self):
    topLayout=qtw.QVBoxLayout()
    
    self.progress=qtw.QLabel()
    topLayout.addWidget(self.progress)
    
    self.nextEventTime=qtw.QLabel()
    topLayout.addWidget(self.nextEventTime)
    
    self.match=qtw.QLabel()
    topLayout.addWidget(self.match)
    self.line=qtw.QLabel()
    topLayout.addWidget(self.line)
    
    self.videoLink=qtw.QLabel()
    self.videoLink.setOpenExternalLinks(True)
    topLayout.addWidget(self.videoLink)
    
    layoutVotes=qtw.QGridLayout()
    
    #Add header
    counNameHeader=qtw.QLabel("Councilor")
    yesHeader=qtw.QLabel("Yes")
    noHeader=qtw.QLabel("No")
    absentHeader=qtw.QLabel("Absent")
    
    layoutVotes.addWidget(counNameHeader,0,0)
    layoutVotes.addWidget(yesHeader,0,1)
    layoutVotes.addWidget(noHeader,0,2)
    layoutVotes.addWidget(absentHeader,0,3)
    
    #add one row for each councilor
    self.councilorVotes={}
    count=1
    councilors=self.database["councilors"]
    radioButtonStyleStr="QRadioButton::indicator {width: 20px;height: 20px;}"
    for key in councilors.keys():
      
      radioGroup=qtw.QButtonGroup(self)
      counNameStr=councilors[key]["name"]
      self.councilorVotes[counNameStr]=radioGroup
      counName=qtw.QLabel(counNameStr)
      
      yesVote=qtw.QRadioButton()
      yesVote.selection="yes"
      yesVote.setChecked(True)
      yesVote.setStyleSheet(radioButtonStyleStr)
      
      noVote=qtw.QRadioButton()
      noVote.selection="no"
      noVote.setStyleSheet(radioButtonStyleStr)
      
      absent=qtw.QRadioButton()
      absent.selection="absent"
      absent.setStyleSheet(radioButtonStyleStr)
      
      layoutVotes.addWidget(counName,count,0)
      layoutVotes.addWidget(yesVote,count,1)
      layoutVotes.addWidget(noVote,count,2)
      layoutVotes.addWidget(absent,count,3)
      
      radioGroup.addButton(yesVote)
      radioGroup.addButton(noVote)
      radioGroup.addButton(absent)
      
      count+=1
    topLayout.addLayout(layoutVotes)
    
    self.motionLink=qtw.QLineEdit()
    self.motionLink.setStyleSheet(backGroundStyle)
    self.motionLink.setPlaceholderText("Paste link to agenda item")
    topLayout.addWidget(self.motionLink)
    
    self.motionTitle=qtw.QLineEdit()
    self.motionTitle.setStyleSheet(backGroundStyle)
    self.motionTitle.setPlaceholderText("Motion title")
    topLayout.addWidget(self.motionTitle)
    
    layoutNewTime=qtw.QHBoxLayout()
    newTimePrompt=qtw.QLabel("Update time:")
    layoutNewTime.addWidget(newTimePrompt)
    self.newVideoTime=qtw.QLineEdit()
    self.newVideoTime.setStyleSheet(backGroundStyle)
    self.newVideoTime.setPlaceholderText("HH:MM:SS")
    layoutNewTime.addWidget(self.newVideoTime)
    topLayout.addLayout(layoutNewTime)
    
    layoutSubmit=qtw.QHBoxLayout()
    
    #skipButton=qtw.QPushButton("Skip")
    #skipButton.clicked.connect(self.skipClicked)
    #layoutSubmit.addWidget(skipButton)
    
    removeButton=qtw.QPushButton("Remove event")
    removeButton.clicked.connect(self.removeClicked)
    layoutSubmit.addWidget(removeButton)
    
    nextButton=qtw.QPushButton("Add vote")
    nextButton.clicked.connect(self.addVoteClicked)
    layoutSubmit.addWidget(nextButton)
    
    topLayout.addLayout(layoutSubmit)
    self.addVotewidget=qtw.QWidget()
    self.addVotewidget.setStyleSheet(backGroundStyle)
    self.addVotewidget.setLayout(topLayout)
    
    self.centralWidget.addWidget(self.addVotewidget)
  def updateAddVoteWidget(self):
    
    hadVoteTime=False
    if self.currentVideo!=None:
      
      video=self.database["videos"][self.currentVideo]
      
      if not (str(self.currentTime) in video["voteTimes"].keys()):
        self.incrementCurrentTimeIndex()
      
      if self.currentVideo!=None:
        video=self.database["videos"][self.currentVideo]
          
        hadVoteTime=True
        voteTime=video["voteTimes"][str(self.currentTime)]
        timeDict=voteTime["time"]
        t=getTotalSeconds(timeDict)
        matchWord=voteTime["wordMatched"]
        matchedLinePrev=voteTime["matchedLinePrev"]
        matchedLineCur=voteTime["matchedLineCur"]
        matchedLineNext=voteTime["matchedLineNext"]
        url=self.currentVideo+"?t="+str(t)
        timeIndex=video["voteTimesOrder"].index(self.currentTime)
        progress=str(timeIndex+1)+"/"+str(len(video["voteTimes"]))
        videoTime=str(timeDict["h"])+":"+str(timeDict["m"])+":"+str(timeDict["s"])
        if timeIndex<len(video["voteTimes"])-1:
          nextTimeSeconds=video["voteTimesOrder"][timeIndex+1]
          nextTimeDict=video["voteTimes"][nextTimeSeconds]["time"]
          nextVideoTime=str(nextTimeDict["h"])+":"+\
            str(nextTimeDict["m"])+":"+str(nextTimeDict["s"])
    if not hadVoteTime:
      url=""
      matchWord=""
      videoTime=""
      nextVideoTime=""
    self.match.setText("Matched: \""+matchWord+"\"")
    self.line.setText("In lines: \""+matchedLinePrev+matchedLineCur+matchedLineNext+"\"")
    self.videoLink.setText("URL at match: <a href='"+url+"'>"+url+"</a>")
    self.progress.setText(progress)
    self.newVideoTime.setText(videoTime)
    self.nextEventTime.setText("Next event time: "+nextVideoTime)
  def addVoteClicked(self):
    
    if "motions" in self.database.keys():
      motions=self.database["motions"]
    else:
      self.database["motions"]={}
      motions=self.database["motions"]
    
    #print()
    #print("-----------------------")
    councilorVotes=[]
    for councilor in self.councilorVotes.keys():
      
      button=self.councilorVotes[councilor].checkedButton()
      #print(councilor+" "+str(button.selection))
      councilorVotes.append((councilor,str(button.selection)))
    
    #NOTE: update to new time
    newTime=dt.datetime.strptime(self.newVideoTime.text(),"%H:%M:%S")
    newTimeDict={"h":newTime.hour,"m":newTime.minute,"s":newTime.second}
    newTimeSecondsTotal=str(getTotalSeconds(newTimeDict))
    
    video=self.database["videos"][self.currentVideo]
    currentTimeIndex=video["voteTimesOrder"].index(self.currentTime)
    currentVoteTime=video["voteTimes"][self.currentTime]
    newVoteTime=copy.deepcopy(currentVoteTime)
    newVoteTime["time"]=newTimeDict
    video["voteTimes"].pop(self.currentTime)
    video["voteTimes"][newTimeSecondsTotal]=newVoteTime
    
    self.currentTime=newTimeSecondsTotal
    video["voteTimesOrder"][currentTimeIndex]=newTimeSecondsTotal
    
    motionID=self.getNewMotionID()
    video["voteTimes"][newTimeSecondsTotal]["motion"]=motionID
    motion={"video":self.currentVideo,"voteTime":newTimeSecondsTotal}
    motion["councilorVotes"]=councilorVotes
    #print(self.motionLink.text())
    #print(self.newVideoTime.text())
    motion["agendaLink"]=self.motionLink.text()
    motion["title"]=self.motionTitle.text()
    motions[motionID]=motion
    self.motionLink.setText("")
    self.motionTitle.setText("")
    self.incrementCurrentTimeIndex()
    self.updateAddVoteWidget()
  def skipClicked(self):
    self.incrementCurrentTimeIndex()
    self.updateAddVoteWidget()
  def removeClicked(self):
    
    video=self.database["videos"][self.currentVideo]
    
    currentTime=self.currentTime
    self.incrementCurrentTimeIndex()
    
    currentTimeIndex=video["voteTimesOrder"].index(currentTime)
    video["voteTimes"].pop(currentTime)
    del video["voteTimesOrder"][currentTimeIndex]
    
    self.updateAddVoteWidget()
  def getNewMotionID(self):
    nextID=self.database["nextMotionID"]
    self.database["nextMotionID"]+=1
    return nextID
  def incrementCurrentTimeIndex(self):
    
    video=self.database["videos"][self.currentVideo]
    currentIndex=video["voteTimesOrder"].index(self.currentTime)
    currentIndex+=1
    
    if currentIndex>=len(video["voteTimes"]):
      video["status"]="processed"
      videoSet=self.attemptToSetCurrentVideoToAnUnprocessedVideo()
      if not videoSet:
        self.switchToAddVideoMode()
        self.showStatusMessage("No videos to process, try adding one")
      else:
        self.showStatusMessage("Video proccessed, starting new video")
    else:
      self.currentTime=video["voteTimesOrder"][currentIndex]
      self.database["currentTime"]=self.currentTime
  def addVideoTaskClicked(self):
     self.switchToAddVideoMode()
  def addVotesTaskClicked(self):
    if self.hasUnprocessedVideos():
      self.switchToAddVoteMode()
    else:
      self.switchToAddVideoMode()
      self.showStatusMessage("No unprocessed videos, can't add votes.")
  def addVideoButtonClicked(self):
    
    text=self.addVideoText.text()
    date=self.addVideoDate.date()
    dateDict={"year":date.year(),"month":date.month(),"day":date.day()}
    parsed=urlp.urlparse(text)
    
    #TODO: this is very basic and insufficient URL validation
    isURL=False
    if parsed.scheme and parsed.netloc:
      isURL=True
    
    if isURL:
      newParsed=(parsed.scheme,parsed.netloc,parsed.path,None,None,None)
      url=urlp.urlunparse(newParsed)
      print(str(parsed))
      if "videos" in self.database.keys():
        videos=self.database["videos"]
      else:
        self.database["videos"]={}
        videos=self.database["videos"]
      #id=len(videos)
      if url in videos.keys():
        self.showStatusMessage("Video already in database")
      else:
        videos[url]={"status":"unprocessed","date":dateDict}
        self.showStatusMessage("Added video with url="+url)
        self.switchToAddVoteMode()
    else:
      #self.switchToNotificationMode("The entered url=\""+text+
      #  "\" doesn't look like a url, try adding a video url again")
      self.showStatusMessage("The entered url=\""+text+
        "\" doesn't look like a url, try adding a video url again")
  def loadDatabase(self):
    self.databaseFileName="../data/database.json"
    try:
      file=open(self.databaseFileName,"r")
      self.database=json.load(file)
      file.close()
      
      db=self.database
      for key in db.keys():
        print(str(key)+":"+str(db[key]))
    except FileNotFoundError:
      self.initDatabase()
  def initDatabase(self):
    self.database={
      "councilors":{
        0:{"name":"Sam Austin"},
        1:{"name":"Shawn Cleary"},
        2:{"name":"Patty Cuttell"},
        3:{"name":"Cathy Deagle Gammon"},
        4:{"name":"Andy Fillmore"},
        5:{"name":"Billy Gillis"},
        6:{"name":"Nancy Hartling"},
        7:{"name":"David Hendsbee"},
        8:{"name":"Virgina Hinch"},
        9:{"name":"Becky Kent"},
        10:{"name":"Tony Mancini"},
        11:{"name":"Kathryn Morse"},
        12:{"name":"Jean St-Amand"},
        13:{"name":"Janet Steele"},
        14:{"name":"John Young"},
        15:{"name":"Trish Purdy"},
        16:{"name":"Laura White"}
        },
      "matchWords":["[ Voting in Progress ]",
                    "vote",
                    "carries","approved","passes","fails"
                    ],
      "currentVideo":None,
      "currentTime":None,
      "nextMotionID":0,
      "nextCouncilorID":17,
      "minSecondsBetweenVoteEvents":30
    }
  def writeDatabase(self):
    file=open("../data/database.json",'w')
    json.dump(self.database,file,indent=2)
def main():
  
  minutes_resp = requests.get('https://pub-halifax.escribemeetings.com/Meeting.aspx?Id=7ec924d6-96b8-4dec-b65a-d1d6ce3e43fa&Agenda=Agenda&lang=English&Item=37&Tab=attachments')
  minutes_html = lxml.html.fromstring(minutes_resp.text)
  pdf_links = [
    urlp.urljoin(minutes_resp.url, href)
    for href in minutes_html.xpath('//a[contains(@class, "Link") and @tabindex]/@href')
    if 'player' not in href.lower()
  ]

  for pdf_link in pdf_links:
    pdf_response = requests.get(pdf_link)
    print(pdf_link, pdf_response.headers['content-type'], pdf_response.headers['content-disposition'], pdf_response.content[:10])
    time.sleep(30) # Be polite!
  
  quit()
  '''
  f = tempfile.NamedTemporaryFile()
  f.write(pdf_response.content)
  f.flush()
  pdf = pypdf.PdfReader(f.name)
  len(pdf.pages)
  pdf.pages[0].extract_text()[:200]
  '''
  
  '''
  #TODO: only parse a video url when we get to it, e.g. if we finish one link go to the next
  urls=[
    "https://youtube.com/live/VxEmLK7FeJY",
    #"https://youtube.com/live/ypY_-hFZLbQ",
    #"https://youtube.com/live/C4NqzWRCtTo",
    #"https://youtube.com/live/uHUqJaufUUc",
    #"https://youtube.com/live/pETrvSz-LCU"
  ]
  voteTimeUrls=[]
  for url in urls:
    print("downloading subtitles for "+str(url)+" ...")
    title=getTitle(url)
    print("title="+str(title))
    downloadSubTitles(url)
    voteTimeUrls=voteTimeUrls+getVotetimes(url)
  '''
  #voteTimeUrls,database
  
  app = qtw.QApplication(sys.argv)
  window = MainWindow()
  window.show()
  app.exec()
  window.writeDatabase()
if __name__=="__main__":
  main()

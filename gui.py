#from PySide6.QtWidgets import QApplication, QWidget
import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
import PySide6.QtGui as qtg
import sys
import subprocess as sp
import datetime as dt
import json
councilors=[
  "Sam Austin",
  "Shawn Cleary",
  "Patty Cuttell",
  "Cathy Deagle Gammon",
  "Andy Fillmore",
  "Billy Gillis",
  "Nancy Hartling",
  "David Hendsbee",
  "Virgina Hinch",
  "Becky Kent",
  "Tony Mancini",
  "Kathryn Morse",
  "Jean St-Amand",
  "Janet Steele",
  "John Young",
  "Trish Purdy",
  "Laura White"
  ]

motionVoteDatabase={}

class Context():
  def __init__(self):
    

def downloadSubTitles(url,outFileName="temp"):
  cmd=["yt-dlp","--skip-download","--write-subs",
       "--sub-langs", "en","--write-auto-subs",
       "-o",outFileName,url]
  result=sp.run(cmd,capture_output=True)
  if result.returncode!=0:
    print("rc="+str(result.returncode))
    print("stdout="+str(result.stdout))
    print("stderr="+str(result.stderr))
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

class MainWindow(qtw.QMainWindow):
  def __init__(self,context):
    super().__init__()
    
    self.context=context
    
    self.voteTimeUrls=voteTimeUrls
    self.currentVoteTimeUrl=0
    
    self.setWindowTitle("My App")
    layoutAll=qtw.QVBoxLayout()
    
    self.videoLink=qtw.QLabel()
    self.videoLink.setOpenExternalLinks(True)
    layoutAll.addWidget(self.videoLink)
    self.setVideoLink()
    
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
    for i in range(len(councilors)):
      
      radioGroup=qtw.QButtonGroup(self)
      self.councilorVotes[councilors[i]]=radioGroup
      counName=qtw.QLabel(councilors[i])
      yesVote=qtw.QRadioButton()
      yesVote.selection="yes"
      yesVote.setChecked(True)
      noVote=qtw.QRadioButton()
      noVote.selection="no"
      absent=qtw.QRadioButton()
      absent.selection="absent"
      layoutVotes.addWidget(counName,i+1,0)
      layoutVotes.addWidget(yesVote,i+1,1)
      layoutVotes.addWidget(noVote,i+1,2)
      layoutVotes.addWidget(absent,i+1,3)
      radioGroup.addButton(yesVote)
      radioGroup.addButton(noVote)
      radioGroup.addButton(absent)
    
    layoutAll.addLayout(layoutVotes)
    
    
    #date=qtw.QCalendarWidget()
    #layoutAll.addWidget(date)
    
    
    layoutSubmit=qtw.QHBoxLayout()
    
    skipButton=qtw.QPushButton("Skip")
    skipButton.clicked.connect(self.skipClicked)
    layoutSubmit.addWidget(skipButton)
    
    nextButton=qtw.QPushButton("Next")
    nextButton.clicked.connect(self.nextClicked)
    layoutSubmit.addWidget(nextButton)
    
    layoutAll.addLayout(layoutSubmit)
    
    widget=qtw.QWidget()
    widget.setLayout(layoutAll)
    
    # Set the central widget of the Window.
    self.setCentralWidget(widget)
  def setVideoLink(self):
    url=self.voteTimeUrls[self.currentVoteTimeUrl]
    self.videoLink.setText("<a href='"+url+"'>"+url+"</a>")
  def nextClicked(self):
    url=self.voteTimeUrls[self.currentVoteTimeUrl]
    print()
    print("-----------------------")
    print(str(url))
    print("-----------------------")
    for councilor in self.councilorVotes.keys():
      
      button=self.councilorVotes[councilor].checkedButton()
      print(councilor+" "+str(button.selection))
    self.currentVoteTimeUrl+=1
    self.setVideoLink()
  def skipClicked(self):
    url=self.voteTimeUrls[self.currentVoteTimeUrl]
    print()
    print("-----------------------")
    print(str(url))
    print("-----------------------")
    print("skipped")
    self.currentVoteTimeUrl+=1
    self.setVideoLink()
def loadDatabase():
  file=open("votes1.json")
  voteDatabase=json.load(file)
  for key in voteDatabase.keys():
    print(str(key)+":"+str(voteDatabase[key]))
  return voteDatabase
def writeDatabase(voteDatabase):
  file=open("votes2.json",'w')
  json.dump(voteDatabase,file)
def main():
  
  context=Context()
  
  context.database=loadDatabase()
  
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
  
  #voteTimeUrls,database
  app = qtw.QApplication(sys.argv)
  window = MainWindow(context)
  window.show()
  app.exec()
  
  writeDatabase(database)
if __name__=="__main__":
  main()

__module_name__ = "ZhiRen"
__module_version__ = "0.2.7"
__module_description__ = "Add the nickname at the begining of your words, replace nicknames and numbers with colors"
 
import xchat
import re
 
colors=[19,20,22,24,25,26,27,28,29]
def color_of(str):
	sum=0
	for i in str: sum += ord(i)
	sum %= len(colors)
	return colors[sum]
 
def selectnick(word, word_eol, userdata):
	"""1. select the nickname what you typed\
	   2. color any nicks of the channel if the nick is\
	      displayed in your typed message"""
	# If this window is a Channel, whose name begins with '#',
	# then activate this script, otherwise, return None.
	CHANNAME=xchat.get_context().get_info('channel')
	if not re.search('^#.*',CHANNAME): return None
 
	# Ignore '!,@,~' begins 
	if re.search('^[~!@].*',word_eol[0]): return None
 
	# Detect whether the first word is nickname or not
	NICKS = [i.nick for i in xchat.get_list("users")]
	if "," in word_eol[0]:
		RAW=word_eol[0].split(",",1)
		NAME=RAW[0]
		if NAME in NICKS: 
			WORD=RAW[1].strip()
		else:
			NAME=""
			WORD=word_eol[0]
	else:
		NAME=""
		WORD=word_eol[0]
	# Select the typed nickname
	for i in NICKS:
		if NAME==i: xchat.command("USELECT %s"%(NAME,))
 
	# Gather all the nicks selected
	SELECTNICKS = [j.nick for j in xchat.get_list("users") if j.selected==1]
 
	# Set Style
	if len(SELECTNICKS) > 0:
		STYLE = "%s: "% ",".join(SELECTNICKS)
	else: STYLE = ""
 
	# Combine words
	SENTENCE=STYLE+WORD
 
	#==================================================
	# Replace all the nicknames existed and all numbers
	# \002: bold
	# \003: color
	# \007: space
	# begin and end both need add '\003'
	#==================================================
 
	# Sort the Nicks by length, for eliminate some bugs.
	# long nickname -> short nickname
	CMP=lambda x,y: len(y)-len(x)
	NICKS.sort(CMP)
 
	# Create hashtable for the nicks
	#   0     1     2    3              0           1          2    3
	# (nick,regex,hash,color) ==== ('foo-bar','foo\\-bar',143512543,23)
	NICKHASH=[]
	for i in NICKS:
		regex=re.sub('(\-|\||\[|\]|\_|\^|\$|\.|\\|\<|\>|\(|\)|\+|\?|\{|\}|%)',r'\\\1',i)
		NICKHASH.append((i,regex,hash(i),color_of(i)))
 
	# Replace the nickname with hash value
	cpnchar='([^a-zA-Z0-9])'
	for i in NICKHASH:
		SENTENCE=re.sub(cpnchar+i[1],'\\1'+'['+'%d'%(i[2],)+']',SENTENCE)
		SENTENCE=re.sub(i[1]+cpnchar,'['+'%d'%(i[2],)+']'+'\\1',SENTENCE)
 
	# Replace all the numbers you typed with color
	NumColor='04' # 04: Red color
	# When those characters are near to numbers, do not color the numbers 
	IgnoreChar='([a-zA-Z\d/&=+\?\.:\[\]\-\(\)\|\_\%])'
	# Paint All the numbers in the sentence with color	
	PaintNum='\\003'+NumColor+'\\1'+'\\003'
	SENTENCE=re.sub('(\d+)',PaintNum,SENTENCE)
	# Remove all the number's color if ignore words near the numbers
	RegexL=IgnoreChar+'\\003'+'\d\d'+'(\d+)'+'\\003'
	RegexR='\\003'+'\d\d'+'(\d+)'+'\\003'+IgnoreChar
	SENTENCE=re.sub(RegexL,'\\1\\2',SENTENCE)
	SENTENCE=re.sub(RegexR,'\\1\\2',SENTENCE)
 
	# Replace those '[1232353]' like numbers with colorful nickname
	for i in NICKHASH:
		COLORNUM = i[3]
		COLOR = '%.2d'%(COLORNUM,)
		COLORNICK='\\003'+COLOR+i[0]+'\\003'
		SENTENCE=re.sub('\['+'%d'%(i[2],)+'\]',COLORNICK,SENTENCE)
 
	# Send the word to channel
	COMMAND="MSG %s %s"%(xchat.get_info("channel"), SENTENCE)
	xchat.command(COMMAND)
 
	# Hook the original behavior
	return xchat.EAT_ALL
 
def ClearSelect(word, word_eol, userdata):
	"""if you press the key 'ESC', then cancel the select"""
	if word[0]=="65307": xchat.command("USELECT")
 
xchat.hook_command("", selectnick)
xchat.hook_print("Key Press",ClearSelect)

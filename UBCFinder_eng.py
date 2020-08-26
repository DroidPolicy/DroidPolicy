#!/usr/bin/env python
# -*- coding: utf-8 -*-
#=========================================================================
#
#
# Author: xxx
# Date: 2018-08-13:8:14:12
#
#=========================================================================

from __future__ import print_function
from __future__ import division

import os
import sys
import jieba
import MySQLdb
curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(curdir)

if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")
  

from absl import flags
from absl import logging

FLAGS = flags.FLAGS
import synonyms  # https://github.com/huyingxi/Synonyms
import numpy
import unittest

compare_ = lambda x,y,z: "%s vs %s: %f" % (x, y, synonyms.compare(x, y, seg=z)) + "\n" +"*"* 30 + "\n"

stopwords = []
for word in open('stopwords.txt', 'r'):
    stopwords.append(word.strip())

def is_in_sentence(sen2,mywords):
    i = 0
    for myword in mywords:
        if myword in sen2:
            i = 1
            break
    return i

def is_in_list(s2,mywords):
    i = 0
    for words in s2:
        for myword in mywords:
            if myword == words or myword+"s" == mywords or myword+"es" == mywords or myword+"d" == mywords or myword+"ed" == mywords:
                i = 1
                break
    return i

def is_sort(interval,s2,mywords1,mywords2):
    list1 = []
    list2 = []
    for myword1 in mywords1:
        for j in range(len(s2)):
            if myword1 in s2[j]:
                # print (j)
                list1.append(j)

    for myword2 in mywords2:
        for m in range(len(s2)):
            if myword2 in s2[m]:
                # print ('aaa')
                # print (m)
                list2.append(m)

    i = 0
    for listnum1 in list1:
        for listnum2 in list2:
            if (listnum2-listnum1) > 0 and (listnum2-listnum1)<=interval:
                i = 1
                break
    # print(i)
    return i

def detect(sen2):
	s2 = sen2.split(' ')
	n = 0
	while 1:
		if n >= len(s2):
			break
		else:
			if s2[n] in stopwords:
				s2.remove(s2[n])
				n = 0
			else:
				n = n + 1
				
	if len(s2) > 0:
		# print(s2)
		result = ''

		# 1、ad disruption
		adrule1 = is_in_list(s2, ["ads"])
		if adrule1 == 1 and "notification" not in sen2:
			result = result + ',' + "(ad disruption)"

		# 2、virus
		virusrule1 = is_in_list(s2, ["virus"])
        	virusrule12 = is_in_list(s2, ["trojan"])
        	virusrule3 = is_in_list(s2, ["malware"])
		if (virusrule1+virusrule2+virusrule3) != 0:
			result = result + ',' + "(virus)"

		# 3、privacy leak
		privacyrule1 = is_sort(3, s2, ["steal"], ["info"])
        	privacyrule2 = is_sort(3, s2, ["steal"], ["information"])
        	privacyrule3 = is_sort(4, s2, ["steal"], ["data"])
        	privacyrule4 = is_sort(3, s2, ["steal"], ["file"])
        	privacyrule5 = is_sort(4, s2, ["data"], ["miss"])
        	privacyrule6 = is_sort(5, s2, ["photo"], ["miss"])
		privacyrule7 = is_sort(7, s2, ["file"], ["miss"])
		privacyrule8 = is_sort(6, s2, ["backup"], ["miss"])
		privacyrule9 = is_sort(4, s2, ["data"], ["lost"])
        	privacyrule10 = is_sort(5, s2, ["photo"], ["lost"])
		privacyrule11 = is_sort(6, s2, ["file"], ["lost"])
		privacyrule12 = is_sort(7, s2, ["backup"], ["lost"])
		if (privacyrule1+privacyrule2+privacyrule3+privacyrule4+privacyrule5+privacyrule6+privacyrule7+privacyrule8+privacyrule9+privacyrule10+privacyrule11+privacyrule12) != 0:
			result = result + ',' + "(privacy leak)"

		# 4、browser
		browserrule1 = is_sort(2, s2, ["modify"], ["browser"])
		browserrule2 = is_sort(2, s2, ["modify"], ["bookmark"])
		browserrule3 = is_sort(2, s2, ["hijack"], ["browser"])
        	browserrule4 = is_sort(2, s2, ["hijack"], ["bookmark"])
		if (browserrule1+browserrule2+browserrule3+browserrule4) != 0:
			result = result + ',' + "(browser)"

		# 5、bad performance
		performrule1 = is_sort(3, s2, ["phone"], ["crash"])
        	performrule2 = is_sort(3, s2, ["phone"], ["stuck"])
        	performrule3 = is_sort(3, s2, ["signal"], ["weak"])
        	performrule4 = is_sort(3, s2, ["wifi"], ["weak"])
        	performrule5 = is_sort(3, s2, ["CPU"], ["slow"])
        	performrule6 = is_sort(3, s2, ["consume"], ["battery"])
		if (performrule1+performrule2+performrule3+performrule4+performrule5+performrule6) != 0:
			result = result + ',' + "(bad performance)"

		# 6、payment
		behavior61 = is_in_list(s2, ["fraud", "cheat", "deceive"])
        	behavior62 = is_in_list(s2, ["bill", "money", "payment", "$"])
		
		if behavior61 == 1 and behavior62 == 1:
			result = result + ',' + "(payment)"

		# 7、network traffic
		behavior71 = is_in_list(s2, ["network", "traffic"])
        	behavior72 = is_similar(s2, ["consume"])
		
		if behavior71 == 1 and behavior72 == 1:
			result = result + ',' + "(network traffic)"
		
		# 8、drive-by download
		behavior81 = is_in_list(s2, ["download", "install"])
        	behavior82 = is_in_list(s2, ["app", "plug-in", "it"])
        	behavior83 = is_in_list(s2, ["force", "let", "induce"])

		if behavior81 == 1 and behavior82 == 1 and behavior83 == 1:
			result = result + ',' + "(drive-by download)"

		# 9、hidden app
		behavior91 = is_in_list(s2, ["icon", "app"])
        	behavior92 = is_in_list(s2, ["disappear", "hidden", "not find"])
		if behavior91 == 1 and behavior92 == 1:
			result = result + ',' + "(hidden app)"
		

		# 10、fail to uninstall
		behavior100 = is_in_list(s2, ["fail"])
        	behavior101 = is_in_list(s2, ["cannot"])
        	behavior102 = is_in_list(s2, ["how"])
        	behavior103 = is_in_list(s2, ["forbid"])
        	behavior104 = is_in_list(s2, ["uninstall", "remove"])
        	behavior105 = is_sort(2, s2, ["cannot"], ["uninstall", "remove"])
        	behavior106 = is_sort(2, s2, ["how"], ["uninstall", "remove"])
        	behavior107 = is_sort(3, s2, ["fail"], ["uninstall", "remove"])
        	behavior108 = is_sort(3, s2, ["uninstall", "remove"], ["fail"])
        	behavior109 = is_sort(3, s2, ["forbid"], ["uninstall", "remove"])
        	behavior110 = is_sort(3, s2, ["uninstall", "remove"], ["forbid"])
		if behavior100 == 1 and behavior104 == 1 and (behavior107 == 1 or behavior108 == 1):
			result = result + ',' + "(fail to uninstall)"
		elif behavior103 == 1 and behavior104 == 1 and (behavior109 == 1 or behavior110 == 1):
			result = result + ',' + "(fail to uninstall)"
		elif behavior101 == 1 and behavior104 == 1 and behavior105 == 1:
			result = result + ',' + "(fail to uninstall)"
		elif behavior102 == 1 and behavior104 == 1 and behavior106 == 1:
			result = result + ',' + "(fail to uninstall)"
			
		# 11、powerboot
		behavior110 = is_in_list(s2, ["powerboot"])
		if behavior110 == 1:
			result = result + ',' + "(powerboot)"

		# 12、fail to start
		behavior120 = is_in_list(s2, ["crash", "stuck"])
        	behavior121 = is_in_list(s2, ["stop"])
        	behavior122 = is_in_list(s2, ["running"])
        	behavior123 = is_in_list(s2, ["fail", "cannot"])
        	behavior124 = is_in_list(s2, ["start"])
        	behavior125 = is_sort(2, s2, ["fail", "cannot"], ["start"])
        	behavior126 = is_in_list(s2, ["exception"])
		if behavior120 == 1 and "phone" not in sen2:
			result = result + ',' + "(fail to start)"
		elif behavior121 == 1 and behavior122 == 1:
			result = result + ',' + "(fail to start)"
		elif behavior123 == 1 and behavior124 == 1 and behavior125 == 1:
			result = result + ',' + "(fail to start)"
		elif behavior126 == 1:
			result = result + ',' + "(fail to start)"

		# 13、fail to exit
		behavior130 = is_in_list(s2, ["cannot", "exit", "close", "shut"])
        	behavior131 = is_sort(2, s2, ["cannot"], ["exit", "close", "shut"])
		if behavior130 == 1 and behavior131 == 1:
			result = result + ',' + "(fail to exit)"

		# 14、 retrieve content
		behavior140 = is_in_list(s2, ["404", "blank"])
        	behavior141 = is_in_list(s2, ["fail", "cannot", "data"])
        	behavior142 = is_sort(2, s2, ["fail", "cannot"], ["data"])
		
		if behavior140 == 1:
			result = result + ',' + "(retrieve content)"
		elif behavior141 == 1 and behavior142 == 1:
			result = result + ',' + "(retrieve content)"

		# 15、notification ad
		behavior150 = is_in_list(s2, ["notification"])
        	behavior151 = is_in_list(s2, ["ad", "ads", "full", "remove"])
		if behavior150 == 1 and behavior151 == 1:
			result = result + ',' + "(notification ad)"

		# 16、fail to login
		behavior160 = is_in_list(s2, ["cannot", "fail", "how"])
        	behavior161 = is_in_list(s2, ["login", "register"])
		if behavior160 == 1 and behavior161 == 1:
			result = result + ',' + "(fail to login)"
		
		# 17、add shortcuts
		behavior170 = is_in_list(s2, ["add", "create"])
        	behavior171 = is_in_list(s2, ["shortcut", "icon"])
		if behavior170 == 1 and behavior171 == 1:
			result = result + ',' + "(add shortcuts)"

		# 18、fail to install
		behavior180 = is_in_list(s2, ["cannot", "fail", "how"])
        	behavior181 = is_in_list(s2, ["install"])
		if behavior180 == 1 and behavior181 == 1:
			result = result + ',' + "(fail to install)"

		# 19、redirection
		behavior190 = is_in_list(s2, ["redirect"])
        	behavior191 = is_in_list(s2, ["other"])
		if behavior190 == 1 and behavior191 == 1:
			result = result + ',' + "(redirection)"

		# 20、vulgar content
		behavior200 = is_in_sentence(sen2, [" nude", "masturbat", "racist", " porn", "creep", "pervert", "pedophile", "horny", "penis", " dick", " sex"])
		if behavior200 == 1:
			result = result + ',' + "(vulgar content)"

		# 21、inconsistency
		behavior210 = is_in_list(s2, ["inconsistent"])
        	behavior211 = is_in_list(s2, ["not"])
        	behavior212 = is_in_list(s2, ["describe"])
		if behavior210 == 1:
			result = result + ',' + "(inconsistency)"
		elif behavior211 == 1 and behavior212 == 1:
			result = result + ',' + "(inconsistency)"

		# 22、background
		behavior220 = is_in_list(s2, ["itself", "background", "alwalys"])
        	behavior221 = is_in_list(s2, ["download", "sms", "backup"])
		if behavior220 == 1 and behavior221 == 1:
			result = result + ',' + "(background)"

		# 23、permission abuse
		behavior230 = is_sort(3, s2, ["ask", "unnecessary"], ["permission"])
		behavior231 = is_sort(3, s2, ["require", "need", "want", "give"], ["permission", "access to"])
		behavior232 = is_sort(3, s2, ["permission", "access to"], ["require", "need", " file", "photo", "record", "media", "picture"])
		if behavior230 == 1:
			result = result + ',' + "(permission abuse)"
		elif behavior231 == 1 or behavior232 == 1:
			result = result + ',' + "(permission abuse)"

		# 24、update
		behavior240 = is_sort(3, s2, ["update"], ["other"])
        	behavior241 = is_in_list(s2, ["update", "other"])
		if behavior240 == 1 and behavior241 == 1:
			result = result + ',' + "(update)"

		# 25、repackage
		behavior250 = is_in_list(s2, ["piracy", "repackage", "copy", "plagiarize"])
		if behavior250 == 1:
			result = result + ',' + "(repackage)"
			
		# 26、ranking fraud
		behavior260 = is_in_list(s2, ["comment", "review"])
        	behavior261 = is_in_list(s2, ["fake", "sponsor", "sell", "buy"])
		if behavior260 and behavior261 == 1:
			result = result + ',' + "(ranking fraud)"
			
			
		print(result)
   

if __name__ == '__main__':
    detect('your comment here ')

#! /usr/bin/env python
#
# LulzBot: ufb reborn
#
# SPh, zorg, jaksi, és még sokan mások...

"""
A mindenkori magyarchan kedvenc botja új erőre kapott!

Új parancsok implementálása:
	-Függvény létrehozása:
		-cmd_parancs néven, ha publikus,
		 cmdm_parancs néven, ha csak operátorok számára elérhető, vagy
		 cmda_parancs néven, ha csak az adminok csoportjába tartozó nick-kel, csak operátorok számára elérhető parancsról van szó
		-a következő paraméterekkel:
			-self:
				-self.reply(e, üzenet)
				-self.say_public(üzenet)
			-e:
				-e.type ('privmsg' privát, 'pubmsg' publikus üzenet esetén)
				-e.source:
					-e.source.nick
					-e.source.user
					-e.source.host
			-arguments: string-lista
	-Segítség-szöveg (string) hozzáadása a helps szótárhoz:
		-"parancs": u'segítség'
		-csak azok a parancsok lesznek láthatók a help parancsban, amikhez tartozik bejegyzés
	-FIGYELJ A UNICODE STRINGEKRE:
		-unicode_string = u'árvíztűrő tükörfúrógép'
		-nem_unicode = "flood-tolerant mirror drill"
DOKUMENTÁCIÓ VÉGE, KÉSZ, ENNYI VOLT, NINCS TÖBB
"""

import irc.bot
import irc.strings
import random
import duckduckgo
import urllib2
import re
import collections
import codecs
import time
import HTMLParser
import uf
import subprocess
import sys
import urllib
import os

class ufb(irc.bot.SingleServerIRCBot):
	helps = {
				"help": u'Kilistázza az elérhető parancsokat, vagy segítséget ad egy konkrét parancs használatához',
				"random": u'Csinál valamit valakinek a valamijével. Valahogy.',
				"ping": u'Pong!',
				"summon": u'Megidézheted akár azt is, aki online.',
				"hug": u'Nagyölelés',
				"fuck": u'Sok kutya baszik!',
				"lick": u'Arconnyalás, mit szólsz hozzá?',
				"beer": u'Ha ezt elolvasod, meghívhatod jaksit egy sörre.',
				"tea": u'Baww ;_;',
				"bulimeghivas": u'Kecyjól beoltottad!',
				"ddg": u'KacsaKacsaMegy keresés',
				"yiff": u'Kupakolásra felkészülni',
				"addyiff": u'Ferikép hozzáadása',
				"clop": u'Póniképek',
				"addclop": u'Pónikép hozzáadása',
				"addadmin": u'Admin hozzáadása',
				"addwelcome": u'Köszöntőüzenet hozzáadása',
				"seen": u'Megmondja, hogy az adott személy mikor volt legutóbb online. Használat: seen nick',
				"update": u'Frissíti ufb-t',
				"kocka": u'Dob egy n oldalú kockával',
				"pacsi": u'Minek írok helpet egy ilyen parancshoz?',
				"brohoof": u'Minek írok helpet egy ilyen parancshoz?',
				"debugwelcome": u'SPh kurvája vagyok',
				"mimic": u'kupi barátnő-szimulátora: !mimic Agi-chan',
				"stats": u'kurvára nem működik, ne használd'
			}

	admins = []
	welcomes = collections.defaultdict(list)
	ferikepek = []
	ponikepek = []
	lastseen = {}
	ufgame = None
	garoion = False
	logfile = None
	logfilename = None
	mdict = {}

	def remove_newline(self, text):
		return text.replace(u'\n', u'').replace(u'\r', u'')

	def add_mimic_data(self, name, message):
		words = message.split()
		words_corrected = []
		insert_before = None
		for word in words:
			if word.lower() in [u'a', u'az', u'egy', u'és', u'nem', u'ne']:
				insert_before = word
			elif word.lower() in [u'is', u'se', u'sem']:
				if insert_before:
					words_corrected.append(insert_before + u' ' + word)
					insert_before = None
				elif words_corrected:
					words_corrected[-1] += u' ' + word
				else:
					words_corrected.append(word)
			else:
				if insert_before:
					words_corrected.append(insert_before + u' ' + word)
					insert_before = None
				else:
					words_corrected.append(word)
		words = words_corrected
		if name in self.mdict.keys():
			localresult = self.mdict[name]
		else:
			localresult = {}
		for i in range(len(words) - 1):
			if words[i] in localresult.keys():
				following = localresult[words[i]]
				if words[i + 1] in following.keys():
					following[words[i + 1]] += 1
				else:
					following[words[i + 1]] = 1
			else:
				following = {words[i + 1]: 1}
			localresult[words[i]] = collections.OrderedDict(sorted(following.items(), reverse = True, key = lambda t: t[1]))
			self.mdict[name] = localresult

	def read_file(self):
		file = codecs.open(u'log.txt', "rU", encoding = "utf-8")
		for line in file:
			name = line.split(u': ')[0]
			message = u': '.join(line.split(u': ')[1:])
			self.add_mimic_data(name, message)
		file.close()
		self.mdict = collections.OrderedDict(sorted(self.mdict.items(), reverse = True, key = lambda t: len(t[1])))

	def __init__(self):
		irc.bot.SingleServerIRCBot.__init__(self, [("irc.freenode.net", 6667)], "LulzBot", "LulzBot")
		self.channel = "#magyarchan"
		self.ufgame = uf.ufgame()
		self.logfilename = time.strftime("%Y-%m-%d_%H")
		self.logfile = codecs.open("/www/lulzlog/"+self.logfilename+".txt", "a", encoding = "utf-8")
		self.mdict = {}
		self.read_file()

		with codecs.open(u'admin.txt', "rU", encoding = "utf-8") as file:
			for line in file:
				self.admins.append(self.remove_newline(line).lower())
			file.close()

		with codecs.open(u'feri.txt', "rU", encoding = "utf-8") as file:
			self.ferikepek = [kep.lower() for kep in file.readlines()]
			file.close

		with codecs.open(u'poni.txt', "rU", encoding = "utf-8") as file:
			self.ponikepek = [kep.lower() for kep in file.readlines()]
			file.close

		with codecs.open(u'welcome.txt', "rU", encoding = "utf-8") as file:
			for line in file:
				_n = line.split()[0].lower()
				_m = self.remove_newline(u' '.join(line.split()[1:]))
				self.welcomes[_n].append(_m)

		with codecs.open(u'seen.txt', "rU", encoding = "utf-8") as file:
			for line in file:
				_n = line.split()[0].lower()
				_s = time.localtime(float(line.split()[1]))
				_r = u' '.join(line.split()[2:])
				self.lastseen[_n] = (_s, _r)

	def mimic(self, dict, name):
		if name not in dict.keys():
			return u'Na de mit csinálsz?'
		result = u''
		while len(result) < 200:
			sum = 0
			for v in dict[name].values(): sum += len(v)
			gen = random.randint(0, sum - 1)
			for k, v in dict[name].items():
				if gen < len(v):
					word = k
					break
				else:
					gen -= len(v)
			while word in dict[name].keys():
				result += word + ' '
				sum = 0
				for v in dict[name][word].values(): sum += v
				gen = random.randint(0, sum - 1)
				for k, v in dict[name][word].items():
					if gen < v:
						word = k
						break
					else:
						gen -= v
			result += word + u' '
			word = None
		return result

	def writelog(self, log):
		if time.strftime("%Y-%m-%d_%H") != self.logfilename:
			self.logfilename=time.strftime("%Y-%m-%d_%H")
			self.logfile.close()
			self.logfile = codecs.open("/www/lulzlog/"+self.logfilename+".txt", "a", encoding = "utf-8")
		self.logfile.write(time.strftime("%M:%S")+" - "+log+"\n")
		self.logfile.flush()

	def reply(self, e, message):
		message = self.remove_newline(message)
		if self.garoion:
			message = self.garoi(message)
		for i in range(0, len(message), 350):
			if e.type == 'privmsg':
				self.connection.privmsg(e.source.nick, u'\x0305'+message[i:i+350])
				time.sleep(1)
			else:
				self.connection.privmsg(self.channel, u'\x0305'+e.source.nick+u': '+message[i:i+350])
				time.sleep(1)
				self.writelog(self.connection.get_nickname()+": "+e.source.nick+": "+message)

	def say_public(self, message):
		message = self.remove_newline(message)
		if self.garoion:
			message = self.garoi(message)
		for i in range(0, len(message), 350):
			self.connection.privmsg(self.channel, u'\x0305'+message[i:i+350])
			time.sleep(1)
		self.writelog(self.connection.get_nickname()+": "+message)
		self.add_mimic_data(self.connection.get_nickname(), message)

	def say_private(self, e, message):
		message = self.remove_newline(message)
		if self.garoion:
			message = self.garoi(message)
		for i in range(0, len(message), 350):
			self.connection.privmsg(e, u'\x0305'+message[i:i+350])
			time.sleep(1)

#	def cmd_stats(self, e, args):
#		result = []
#		result += self.ufgame.stats()
#		for _p, _m in result:
#			if _p == "c":
#				self.say_public(_m)
#			elif _p == "p":
#				self.reply(e, _m)
#			else:
#				self.say_private(_p, _m)

	def cmd_mimic(self, e, args):
		if len(args) == 0:
			self.reply(e, self.mimic(self.mdict, e.source.nick))
		else:
			self.reply(e, self.mimic(self.mdict, args[0]))

	def cmd_new(self, e, args):
		result = []
		result += self.ufgame.new(e.source.nick)
		for _p, _m in result:
			if _p == "c":
				self.say_public(_m)
			elif _p == "p":
				self.reply(e, _m)
			else:
				self.say_private(_p, _m)

	def cmd_join(self, e, args):
		result = []
		result += self.ufgame.join(e.source.nick)
		for _p, _m in result:
			if _p == "c":
				self.say_public(_m)
			elif _p == "p":
				self.reply(e, _m)
			else:
				self.say_private(_p, _m)

	def cmd_joint(self, e, args):
		self.cmd_join(e, args)
		self.reply(e, u'Te drogos gecy.')

	def cmd_start(self, e, args):
		result = []
		result += self.ufgame.start(e.source.nick)
		for _p, _m in result:
			if _p == "c":
				self.say_public(_m)
			elif _p == "p":
				self.reply(e, _m)
			else:
				self.say_private(_p, _m)

	def cmd_leave(self, e, args):
		result = []
		result += self.ufgame.leave(e.source.nick)
		for _p, _m in result:
			if _p == "c":
				self.say_public(_m)
			elif _p == "p":
				self.reply(e, _m)
			else:
				self.say_private(_p, _m)

	def cmd_infect(self, e, args):
		if len(args) == 0:
			self.reply(e, u'kit mit hogy?')
			return
		result = []
		result += self.ufgame.infect(e.source.nick, args[0])
		for _p, _m in result:
			if _p == "c":
				self.say_public(_m)
			elif _p == "p":
				self.reply(e, _m)
			else:
				self.say_private(_p, _m)

	def cmd_fertoz(self, e, args):
		self.cmd_infect(e, args)

	def cmd_detect(self, e, args):
		if len(args) == 0:
			self.reply(e, u'kit mit hogy?')
			return
		result = []
		result += self.ufgame.detect(e.source.nick, args[0])
		for _p, _m in result:
			if _p == "c":
				self.say_public(_m)
			elif _p == "p":
				self.reply(e, _m)
			else:
				self.say_private(_p, _m)

	def cmd_latomas(self, e, args):
		self.cmd_detect(e, args)

	def cmd_vote(self, e, args):
		if len(args) == 0:
			self.reply(e, u'kit mit hogy?')
			return
		result = []
		result += self.ufgame.vote(e.source.nick, args[0])
		for _p, _m in result:
			if _p == "c":
				self.say_public(_m)
			elif _p == "p":
				self.reply(e, _m)
			else:
				self.say_private(_p, _m)

	def cmd_kill(self, e, args):
		self.cmd_vote(e, args)

	def cmda_say(self, e, args):
		if len(args)==0:
			self.reply(e, u'Használat: say üzenet')
		else:
			self.say_public(u' '.join(args))

	def cmd_clop(self, e, args):
		if len(self.ponikepek) > 0:
			cloplink = random.choice(self.ponikepek)
		else:
			cloplink = u'Sajnos egy törpelovas linkem sincs pillanatnyilag! Adjál egyet az addclop <link> paranccsal!'
		self.reply(e, cloplink)

	def cmd_kocka(self, e, args):
		max = None
		num = None
		if len(args) == 0:
			args.append('6')
		try:
			max = int(args[0])
			num = random.randint(1, max)
		except:
			self.reply(e, u'Dobás '+args[0]+u' oldalú kockával: 490')
		if max and num:
			if max == 2:
				if num == 1:
					self.reply(e, u'Dobás 2 oldalú kockával: loli')
				else:
					self.reply(e, u'Dobás 2 oldalú kockával: feri')
			else:
				self.reply(e, u'Dobás '+str(max)+u' oldalú kockával: '+str(num))

	def cmdm_addclop(self, e, args):
		if len(args) < 1:
			self.reply(e, u'Használat: addclop link')
		else:
			self.ponikepek.append(args[0])
			with codecs.open(u'poni.txt', "a", encoding = "utf-8") as file:
				file.write(u'\n'+args[0])
				file.close()
			self.reply(e, u'Link hozzáadva!')

	def cmd_yiff(self, e, args):
		msg = u'yaff!'
		if len(self.ferikepek) > 0:
			ferilink = random.choice(self.ferikepek)
		else:
			ferilink = u'Sajnos egy lolifurry linkem sincs pillanatnyilag! Adjál egyet az addyiff <link> paranccsal!'
		self.reply(e, msg)
		self.reply(e, ferilink)

	def cmdm_addyiff(self, e, args):
		if len(args) < 1:
			self.reply(e, u'Használat: addyiff link')
		else:
			self.ferikepek.append(args[0])
			with codecs.open(u'feri.txt', "a", encoding = "utf-8") as file:
				file.write(u'\n'+args[0])
				file.close()
			self.reply(e, u'Link hozzáadva!')

	def cmda_addadmin(self, e, args):
		if len(args) < 1:
			self.reply(e, u'Használat: addadmin nick')
		else:
			self.admins.append(args[0].lower())
			with codecs.open(u'admin.txt', "a", encoding = "utf-8") as file:
				file.write(u'\n'+args[0].lower())
				file.close()
			self.reply(e, u'Admin hozzáadva!')

	def cmdm_addwelcome(self, e, args):
		if len(args) < 2:
			self.reply(e, u'Használat: addwelcome nick köszöntés')
		else:
			self.welcomes[args[0]].append(u' '.join(args[1:]))
			with codecs.open(u'welcome.txt', "a", encoding = "utf-8") as file:
				file.write(args[0]+' '+u' '.join(args[1:])+u'\n')
				file.close()
			self.reply(e, u'Köszöntés hozzáadva!')

	def cmd_help(self, e, arguments):
		if len(arguments) == 0:
			self.reply(e, u'Parancsok: ' + u', '.join(sorted(self.helps.keys())))
		elif len(arguments) == 1:
			if arguments[0] in self.helps:
				self.reply(e, self.helps.get(arguments[0]))
			else:
				self.reply(e, u'Nincs ilyen parancs.')
		else:
			self.reply(e, u'Használat: help [parancs]')

	def cmdm_testmod(self, e, arguments):
		self.reply(e, u'Siker')

	def cmda_testadmin(self, e, arguments):
		self.reply(e, u'Siker')

	def cmd_yaff(self, e, args):
		msg = u'na elég a yiffelésből!'
		self.reply(e, msg)

	def cmd_ping(self, e, args):
		self.say_public(u'Pong!')

	def cmd_summon(self, e, args):
		if len(args) == 0:
			self.say_public(u'Kit akarsz megidézni?')
		else:
			##	if user online minek summonolgatsz
			valsz = random.randint(0,1)
			if valsz:
				self.reply(e, args[0]+u' hamarosan feltűnik.')
			else:
				self.reply(e, args[0]+u' megidézése kudarcba fulladt.')

	def cmd_hug(self, e, args):
		if len(args) < 1:
			self.reply(e, u'kit akarsz megölelni?')
		else:
			self.say_public(u'%s: %s megölelt!' % (args[0],e.source.nick))

	def cmd_fuck(self, e, args):
		if len(args) < 1:
			self.reply(e, u'kit akarsz megkúrni?')
		else:
			self.say_public(u'%s: %s kegyelmet nem ismerve, ordasmód megkúrt!' % (args[0],e.source.nick))

	def cmd_lick(self, e, args):
		if len(args) < 1:
			self.reply(e, u'kit akarsz megnyalni?')
		else:
			if e.source.nick.lower()=='shadowphrogg3264' and args[0].lower()=='agi-chan':
				self.say_public(u'%s: %s indirekt módon pofánnyalt!' % (args[0],e.source.nick))
			else:
				self.say_public(u'%s: %s alattomos módon pofánnyalt!' % (args[0],e.source.nick))

	def cmd_beer(self, e, args):
		if len(args) < 1:
			self.reply(e, u'kivel akarsz sörözni?')
		else:
			self.say_public(u'%s: %s meghívott egy sörre!' % (args[0],e.source.nick))

	def cmd_tea(self, e, args):
		if len(args) < 1:
			self.reply(e, u'kivel akarsz te ázni?')
		else:
			self.say_public(u'%s: %s kiöntötte a lelkét a /t/eádba.' % (args[0],e.source.nick))

	def cmd_bulimeghivas(self, e, args):
		if len(args) < 1:
			self.reply(e, u'kit akarsz meghívni?')
		else:
			self.say_public(u'%s: %s meghívott a következő bulijába!' % (args[0],e.source.nick))

	def cmd_random(self, e, args):
		part1 = [u'kurvára',u'alattomos módon',u'rejtélyesen',u'mocskosul',u'önzetlenül',u'udvariasan',u'humánusan',u'sunyin',u'álnokmód',u'galád módon',u'álszentül',u'titokzatosan',u'sejtelmes módon',u'angyali technikával',u'jámbor szeretettel',u'barátságosan',u'csábosan']
		part2 = [u'fülön',u'taknyon',u'vaginán',u'pocaklakón',u'tarsolyon',u'tenyéren',u'pofán',u'arcon',u'lábon',u'seggen',u'ujjhegyen',u'hajon',u'fejen',u'makkon',u'lábujjon',u'könyökön',u'szemen',u'orron',u'nyelven',u'nyálon',u'homlokon',u'öklön']
		part3 = [u'erőszakolt',u'öklözött',u'hányt',u'térdelt',u'zsályázott',u'szart',u'fosott',u'csókolt',u'maszturbált',u'toszott',u'nyalt',u'ölelt',u'ütött',u'köpött',u'rúgott',u'faszozott',u'vert',u'orrolt',u'fejelt',u'nyelvelt',u'hasalt',u'pofozott',u'kúrt']
		if len(args) < 1:
			self.reply(e, u'kit akarsz random??')
		else:
			self.say_public(args[0]+u': '+e.source.nick+u' '+part1[random.randrange(len(part1))]+u' '+part2[random.randrange(len(part2))]+u' '+part3[random.randrange(len(part3))]+u'!')

	def cmd_ddg(self, e, args):
		if len(u' '.join(args)) == 0:
			self.reply(e, u'Használat: ddg anal bleaching')
		else:
			answer = None
			ddg = duckduckgo.query(" ".join(args).encode("utf-8"), safesearch = False)
			if ddg.answer.text:
				answer = ddg.answer.text
			if not answer and ddg.abstract.text:
				answer = ddg.abstract.text
				if ddg.abstract.url:
					answer += u' ('+ddg.abstract.url+u')'
			if not answer and len(ddg.related):
				if hasattr(ddg.related[0], 'text'):
					if ddg.related[0].text:
						answer = ddg.related[0].text
						if ddg.related[0].url:
							answer += u' ('+ddg.related[0].url+u')'
				elif hasattr(ddg.related[0], 'topics'):
					if len(ddg.related[0].topics) and ddg.related[0].topics[0].text:
						answer = ddg.related[0].topics[0].text
						if ddg.related[0].topics[0].url:
							answer += ddg.related[0].topics[0].url
			if not answer and ddg.definition.text:
				answer = ddg.definition.text
				if ddg.definition.url:
					answer += u' ('+ddg.definition.url+u')'
			if not answer:
				answer = duckduckgo.get_zci(" ".join(args).encode("utf-8"), safesearch=False)
			self.reply(e, HTMLParser.HTMLParser().unescape(answer))

	def cmda_update(self, e, args):
		if len(args) == 0:
			self.reply(e, u'Használat: update url')
		else:
			try:
				urllib.urlretrieve(args[0], u'bot.py.new')
				os.remove(u'bot.py.bak')
				subprocess.Popen([u'python', u'update.py'])
				self.disconnect(u'updating...')
				time.sleep(3)
				sys.exit()
			except:
				self.reply(e, u'Szar a linked')

	def cmd_debugwelcome(self, e, args):
		if len(args) == 0:
			self.reply(e, u'Kit mit hogy?')
		else:
			found = False
			for _k in self.welcomes.keys():
				if re.search(_k, args[0].lower()):
					found = True
					self.reply(e, _k+u': '+random.choice(self.welcomes[_k]))
					break
			if not found:
				self.reply(e, u'hát te meg ki a here vagy? :\\')

	def garoi(self, inputtext):
		rules = [	
					(u'ddzs', u'CCS'),
					(u'dzs', u'CS'),
					(u'ccs', u'DDZS'),
					(u'ddz', u'TSSZ'),
					(u'ggy', u'TTY'),
					(u'lly', u'JJ'),
					(u'ssz', u'ZZ'),
					(u'tty', u'GGY'),
					(u'zzs', u'SS'),
					(u'dj', u'gy'),
					(u'sz', u'Z'),
					(u'ch', u'cs'),
					(u'ts', u'cs'),
					(u'cs', u'DZS'),
					(u'dz', u'TSZ'),
					(u'gy', u'TY'),
					(u'ly', u'J'),
					(u'cc', u'TSSZ'),
					(u'ty', u'GY'),
					(u'zs', u'S'),
					(u'jj', u'LLY'),
					(u'zz', u'SSZ'),
					(u'b', u'P'),
					(u'c', u'TSZ'),
					(u'd', u'T'),
					(u'f', u'V'),
					(u'g', u'K'),
					(u'j', u'LY'),
					(u'k', u'G'),
					(u'p', u'B'),
					(u's', u'ZS'),
					(u's', u'ZZS'),
					(u't', u'D'),
					(u'v', u'F'),
					(u'z', u'SZ'),
					(u'x', u'GZ')
				]
		text = inputtext.lower()
		for _f, _t in rules:
			text = text.replace(_f, _t)
		text = text.lower()
		return text

	def cmd_g(self, e, args):
		if len(args) == 0:
			self.reply(e, u'Használat: g parancs')
		else:
			old = self.garoion
			self.garoion = True
			self.do_command(e, u' '.join(args))
			self.garoion = old

	def cmd_garoi(self, e, args):
		if len(args) == 0:
			if self.garoion:
				self.garoion = False
				self.reply(e, u'Garoi kikapcsolva.')
			else:
				self.garoion = True
				self.reply(e, u'Garoi bekapcsolva.')
		else:
			old = self.garoion
			self.garoion = True
			self.reply(e, u' '.join(args))
			self.garoion = old

	def cmd_pacsi(self, e, args):
		if len(args) == 0:
			self.reply(e, u'Kivel szeretnél pacsizni?')
		else:
			self.say_public(e.source.nick+u' o/\\o '+args[0])

	def cmd_brohoof(self, e, args):
		if len(args) == 0:
			self.reply(e, u'Kivel szeretnél pacsizni?')
		else:
			self.say_public(e.source.nick+u' /)(\\ '+args[0])

	def cmd_seen(self, e, args):
		if len(u' '.join(args)) == 0:
			self.reply(e, u'Használat: seen nick')
		else:
			found = False
			for _n in self.channels[self.channel].users():
				try:
					if re.search(args[0], _n, re.IGNORECASE):
						found = True
						self.reply(e, _n+u' most is itt van!')
						break
				except:
					pass
			if not found:
				for _n in sorted(self.lastseen, key=self.lastseen.get, reverse = True):
					try:
						if re.search(args[0], _n, re.IGNORECASE):
							found = True
							_t, _r = self.lastseen[_n]
							self.reply(e, _n+u' legutóbb ekkor volt online: '+time.strftime("%Y-%m-%d %H:%M:%S", _t)+u' ('+_r+u')')
							break
					except:
						pass
				if not found:
					self.reply(e, args[0]+u' még sosem volt online.')

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")

	def on_welcome(self, c, e):
		c.join(self.channel)
		if len(sys.argv) > 1:
			self.say_public(u'Error: ' + u' '.join(sys.argv[1:]))

	def on_privmsg(self, c, e):
		if e.arguments[0].startswith(u'!'):
			self.do_command(e, e.arguments[0][1:])
		else:
			self.do_command(e, e.arguments[0])

	def on_pubmsg(self, c, e):
		self.add_mimic_data(e.source.nick, e.arguments[0])
		self.writelog(e.source.nick+": "+e.arguments[0])
		if e.arguments[0].startswith(u'!') and len(e.arguments[0]) > 1:
			self.do_command(e, e.arguments[0][1:])
		for i in e.arguments[0].split():
			if re.search(ur'^(^https?://(www\.)?youtube\.com/watch\?.*v=)|(https?://youtu\.be)', i):
				try:
					ufile = urllib2.urlopen(i)
					if ufile.info().gettype() == "text/html":
						data = ufile.read()
						data = unicode(data, "utf-8")
						self.say_public(HTMLParser.HTMLParser().unescape(re.search(ur'<title>[^<]*</title>', data, re.IGNORECASE).group()[7:-8]))
				except IOError:
					pass
		self.lastseen[e.source.nick.lower()] = (time.localtime(time.time()), e.source.nick+u': '+e.arguments[0])
		with codecs.open(u'seen.txt', "w", encoding = "utf-8") as file:
			for _n in self.lastseen.keys():
				_t, _r = self.lastseen[_n]
				file.write(_n+u' '+str(time.mktime(_t))+u' '+_r+u'\n')
			file.close()

	def on_join(self, c, e):
		self.writelog(e.source.nick+" joined.")
		if e.source.nick != c.get_nickname():
			found = False
			for _k in self.welcomes.keys():
				if re.search(_k, e.source.nick.lower()):
					found = True
					self.say_public(random.choice(self.welcomes[_k]))
					break
			if not found:
				self.say_public(u'hát te meg ki a here vagy? :\\')
			self.lastseen[e.source.nick.lower()] = (time.localtime(time.time()), u'belépett a csatornába')
			with codecs.open(u'seen.txt', "w", encoding = "utf-8") as file:
				for _n in self.lastseen.keys():
					_t, _r = self.lastseen[_n]
					file.write(_n+u' '+str(time.mktime(_t))+u' '+_r+u'\n')
				file.close()

	def on_quit(self, c, e):
		self.writelog(e.source.nick+" quit. ("+e.arguments[0]+")")
		self.ufgame.leave(e.source.nick)
		self.lastseen[e.source.nick.lower()] = (time.localtime(time.time()), u'kilépett: '+e.arguments[0])
		with codecs.open(u'seen.txt', "w", encoding = "utf-8") as file:
			for _n in self.lastseen.keys():
				_t, _r = self.lastseen[_n]
				file.write(_n+u' '+str(time.mktime(_t))+u' '+_r+u'\n')
			file.close()

	def on_part(self, c, e):
		self.writelog(e.source.nick+" left.")
		self.ufgame.leave(e.source.nick)
		self.lastseen[e.source.nick.lower()] = (time.localtime(time.time()), u'kilépett a csatornáról')
		with codecs.open(u'seen.txt', "w", encoding = "utf-8") as file:
			for _n in self.lastseen.keys():
				_t, _r = self.lastseen[_n]
				file.write(_n+u' '+str(time.mktime(_t))+u' '+_r+u'\n')
			file.close()

	def on_nick(self, c, e):
		self.writelog(e.source.nick+" changed nick to "+e.target+".")
		self.ufgame.rename(e.source.nick, e.target)
		self.lastseen[e.source.nick.lower()] = (time.localtime(time.time()), u'nicket váltott erre: '+e.target)
		self.lastseen[e.target.lower()] = (time.localtime(time.time()), u'nicket váltott erről: '+e.source.nick)
		with codecs.open(u'seen.txt', "w", encoding = "utf-8") as file:
			for _n in self.lastseen.keys():
				_t, _r = self.lastseen[_n]
				file.write(_n+u' '+str(time.mktime(_t))+u' '+_r+u'\n')
			file.close()

	def on_kick(self, c, e):
		self.writelog(e.source.nick+" kicked "+e.arguments[0]+". ("+e.arguments[1]+")")
		self.ufgame.leave(e.arguments[0])
		if e.arguments[0] == c.get_nickname():
			self.connection.join(self.channel)
		self.lastseen[e.arguments[0].lower()] = (time.localtime(time.time()), e.source.nick+u' kirúgta: '+e.arguments[1])
		with codecs.open(u'seen.txt', "w", encoding = "utf-8") as file:
			for _n in self.lastseen.keys():
				_t, _r = self.lastseen[_n]
				file.write(_n+u' '+str(time.mktime(_t))+u' '+_r+u'\n')
			file.close()

	def on_ctcp(self, c, e):
		pass

	def do_command(self, e, cmd):
		command = cmd.split()[0].lower()
		arguments = cmd.split()[1:]
		try:
			cmd_handler = getattr(self, "cmd_" + command)
			tier = 0
		except:
			try:
				cmd_handler = getattr(self, "cmdm_" + command)
				tier = 1
			except:
				try:
					cmd_handler = getattr(self, "cmda_" + command)
					tier = 2
				except:
					cmd_handler = None
		if cmd_handler:
			if tier == 0:
				cmd_handler(e, arguments)
			elif tier == 1:
				if self.channels[self.channel].is_oper(e.source.nick):
					cmd_handler(e, arguments)
			else:
				if self.channels[self.channel].is_oper(e.source.nick) and e.source.nick.lower() in self.admins:
					cmd_handler(e, arguments)

def main():
	bot = ufb()
	bot.start()

if __name__ == "__main__":
	main()

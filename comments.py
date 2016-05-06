# -*- coding: UTF-8 -*-
import sys
from time import sleep
if sys.version_info[0]==2: #Вот это нужно, чтобы под вторым питоном работал UTF-8
	reload(sys)
	sys.setdefaultencoding('utf-8')
import tabun_api as api
import re
from random import randint
from os.path import exists
user = api.User(login='', passwd='') #Вход
def check(comms): #Получает аргументом список комментов и делает главные штуки
	for c in comms.items():
		comm_id=c[0]
		c=c[1]
		post_id=c.post_id
		was_answered=False #Чтобы не повторяться тут есть эта переменная
		if re.search("@er16 ignore", c.raw_body):
			"""
			Вообще, эта штука переключает игнор
			Ну и тут захардкожено, что файл находится в ./tabun/
			Так что нужно запускать прогу на уровень выше,
			аля python tabun/comments.py
			Тогда игнор будет работать =3
			"""
			for isansw in comms.items():
				answ_id=isansw[0]
				isansw=isansw[1]
				if isansw.parent_id==comm_id and isansw.author==user.username:
					was_answered=True #Вот тут проверка, ответили ли
			if not was_answered:
				"""
				Тут много костылей с файлами
				Ибо оно как-то странно записывает
				Но эт скорее всего я криворукий
				Я ещё за эту часть мне стыдно, да.
				"""
				f=open("tabun/ignore.lst","r+")
				if c.author.strip() in f.read().split("\n"):
					f.close();f=open("tabun/ignore.lst","r") #Если уже есть в списке - убрать
					cutted=re.sub(c.author.strip(),"",f.read())
					f.close()
					f=open("tabun/ignore.lst","w")
					f.write(cutted)
					user.comment(target_id=c.post_id,body="Игнорирование выключено",
							typ="blog",
							reply=comm_id)
				else:
					f.close()
					f=open("tabun/ignore.lst","a") #Ну и соответственно наоборот
					f.write(c.author+"\n")
					user.comment(target_id=c.post_id,body="Игнорирование включено",
							typ="blog",
							reply=comm_id)
				f.close()
				continue

		if re.search("<pre>[\s\S]*</pre>",c.raw_body):
			c.raw_body=re.sub("<pre>[\s\S]*</pre>","",c.raw_body)
		if re.search("<blockquote>[\s\S]*</blockquote>",c.raw_body):
			c.raw_body=re.sub("<blockquote>[\s\S]*</blockquote>","",c.raw_body)
		"""
		^ Вот эти двое вырезают тэги pre и blockquote,
		Там такое неуместно, ибо с о б а ч к и
		"""

		if re.search("@(?P<name>\w+)",c.raw_body): #Главная часть с упоминаниями
			username=list(set(re.findall('@(?P<name>\w+)',c.raw_body)[:10])) #Обрезать до 10 и убрать повторы
			if "am31" in username or "lunabot" in username or "autopilot" in username or "er16" in username: #Не трогать комменты с ботами
				continue
			existing_users=[]
			f=open("tabun/ignore.lst")
			ignored_names=f.read().split("\n") #Получить игнорлист
			f.close()
			for ch in username:
				"""
				Проверяет существование юзера посредством пингования страниц по очереди
				Если выплёвывает ошибку - пропускает
				"""
				try:
					name=user.get_profile(username=ch).username
					if name not in ignored_names:
						existing_users.append(name)
				except api.TabunError:
					pass
			f.close()
			username=existing_users; del existing_users;  # За эту часть мне тоже стыдно, просто так было проще :3
			for isansw in comms.items(): #Тут проверка на ответы
				answ_id=isansw[0]
				isansw=isansw[1]
				if isansw.parent_id==comm_id and (isansw.author==user.username or isansw.author==username):
					was_answered=True
			if not was_answered:
				"""
				Тут генерирует само сообщение
				Я жестко юзал format, ибо нормального
				вставления переменных в строки
				(Слава руби!) нету
				"""
				body=("""Вас упомянул в посте <a href='{post_url}'>'{post_name}'</a> \
		пользователь <ls user="{user_name}" />
		<a href='{comm_url}'>Ссылка</a> на комментарий""".format(
					post_url='/blog/{}/{}.html'.format(c.blog,c.post_id),
					post_name=user.get_post(post_id).title,
					user_name=c.author,
					comm_url="/blog/{blog}/{post_id}.html#comment{comm_id}".format(
						blog=c.blog,
						post_id=c.post_id,
						comm_id=c.comment_id)))
				if len(username)>=1:  #Если есть кому отправить - сделать это
					user.add_talk(talk_users=username,
					title="Упоминание",
					body=body)
				if len(username)>1: #Ну тут уже чисто чтобы выглядело нормально, если больше одного, то пересислить после двоеточия
					cbody="Сообщение об упоминании отправлено пользователям: "
					for x in username:
						cbody+="<a href='/profile/{}'>".format(x)+x+"</a>, "
					cbody=cbody[:-2]
				elif len(username)==1: #Если нет, то просто сказать
					cbody="Сообщение об упоминании отправлено пользователю <a href='/profile/{0}'>{0}</a>".format(username[0])
				else:
					cbody="Ни одного из пользователей, упомянутых в сообщении, не существует или все из них включили игнорирование."
				user.comment(target_id=c.post_id,
				body=cbody,
				typ="blog",
				reply=comm_id) #Доложить, что всё сделано
def run():
	while True: #Бесконечный цикл, чтобы не запускать кроном
		try:
			check(user.get_comments()) #Берёт комменты
			sleep(15) #По идее, чтобы табун не пинал, но я не знаю, пинает или нет :3
		except api.TabunError:
			run()
run()

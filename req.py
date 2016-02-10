# -*- coding: UTF-8 -*-
import time,datetime,re,os,math,sys
try:
	import vk
except:
	raise NameError("No module vk, try \'pip install vk\'")

GROUP_ID=0 #Айдишник группы (НЕ короткое имя)
TOKEN="" #Токен
main_chat_id=0 #ID админконфы

class api:
    def __init__(self, token):
        self.user = vk.API(access_token=token,session=vk.Session(),v=5.14)
        self.last_call = time.time()
        self.calls = 0
        self.method = []

    def __call__(self, **kwargs):
        while 1:
            if time.time()-self.last_call > 1:
                self.calls = 0
                self.last_call = time.time()
            if self.calls < 3:
                self.calls += 1
                r = self.user.__getattr__('.'.join(self.method))(**kwargs)
                self.method = []
                return r

    def __getattr__(self, item):
        self.method.append(item)
        return self

bot = api(TOKEN)

"""
Большущая регулярка, фильтрующая раковые паблики.
Иногда ловит не то, что надо :^)
"""


pattern=re.compile('''(\dch(an)*)|(IGM)|(Системка)|(Изолятор)|(MDK|МДК)|(^#ФАЧ$)|(Орл[её]нок)|(^ХР$)|([а-я]+-ТРЕД)|
((что|ч[её])\sгугл[ия]т)|(Илитач)|((Институт)|(Академия) (Благородных|Порядочных) [А-Я]+)|(ИНДУЛЬГЕНЦИЯ|Индульгенция)|(Подслушано\s*.*)|(i(Face|Feed))|(Лепра)|
(Смешн)|(Шут(\s|ник))|(смех)|(Угар)|(Смейся)|(Улыбн)|(Анекдот)|(Юмор)|(Эй,*\s*принцесса,*\s*меньше стресса)|(абстрактные мемы для элиты всех сортов)|(Лайк(\s|-)Тайм)|(Pepe inc)|([КТ]НН)|(Шкура)|
(JDM™)|(По Кайфу)|(Игроблог)|(Ч[ёео]тки[ей])|(пр[ие]колы*)|(Школа? Не,* не слышали)|(ATLANTA)|([Пп]рогнозы)|([Тт]ипичн)|(^[ЁЕ]П$)|(WOT)|(Вот это)|(Ilita|Илита)|
(мем(сы|ы|есы)*)|(memes)|(#Равновесие)|(sex)|(с(е|э)кс)|((ж|п)оп(ки|а))|(развр)|(гол(ый|ая|ое))|(Порно)|(ДЦП)|(SVLP)|(Пошл[^и]|Непреличн)|(fuck)|
((Список|Списон) дел)|(Мысли)|(Неординарные Суперспсобности)|(Двач)|(НЯШНЫЙ СЕКТОР)|(ЕБС)|(gamechan)|(Кладбище)|
(Подкат[ы|ов])|(МХК)|(Oversee)|(INSTASHIT)|(Men\'s|Мужск)|(Муж[иы]к)|(Феминизма*)|(АНОНИМНЫ[Е|Й])|
(БУГУРТ|Бугурто*)|(Как я встретил столбняк)|(check you)|(Бгхлств)|(Единорог|Конь)|(Ч[ЁО]рный юмор)|(Аморал)|(ПЗДЦ)|(БОРЩ)|((Корпорация|Империя) Зла)|(^#УПРТ$)|(Фабрика)|(Сарказм)|
(Рок)|(Rock)|(Рэп)|(Rap)|(МЫ РУССКИЕ)|(Хикк*ан*)|(нич[еёо]с[ие])|(hentai)|(yaoi|яой)|(убежище)|(MIGHT)|(Оптимист)|(^#Жесткие)|(18\+)|
(DRAGONARTE)|(Nike|Adidas)|(SWAG)|(Больше,*\s*чем просто)|(ж[эе]сть*)|(бляд)|(абсурд)|(^ЕБС$)|(ТЕПЛЫЙ ПАССАЖИР)|(фотошоп)|
(Взрыв Мозга)|(RKVN)|(^Просветлённый$)|(ЗЛОЙ)|(GAMEBOMB)|(это воо*бще)|((^|\s)ниг*г)|(диб)|(funny)|(Пизд)|(геймер)|(Я тебя хочу)|(упоротый)|
(пьяный)|(хован)|(whore)|(моралфаг)|(^ЯД$)|(позор)|(кретин)|(Halvach)|(майдан)''',re.IGNORECASE)

reqs=bot.groups.getRequests(group_id=GROUP_ID,count=20,fields="name,last_name") #Берём заявки + Имя и Фамилия

if reqs['count']>0:
	bot.messages.send(chat_id=main_chat_id,message="Есть заявки") #Если есть заявки - отправляем что-нибудь для предупреждения
else:
	exit(0)
for user in reqs["items"]:
	pts=0 # Очки, изначально 0
	count=0 # Кол-во найденых паблов
	gp = bot.groups.get(user_id=user['id']) # Группы юзера
	send="У ворот "+user["first_name"]+" "+ user["last_name"]+" \n[http://vk.com/id"+str(user["id"])+"]" # Сообщение с информацией о юзере
	gnames="" # Для названий, см. строку 73
	if gp["count"]>1:
		cc=math.floor(gp["count"]/(gp["count"]/10)) #Сколько отнимать за каждый пабл
	else:
		cc=0
	if gp['count']==0: #Если нет подписок - принимать автоматически
		bot.groups.approveRequest(group_id=GROUP_ID,user_id=user['id'])
		send+="\nPubs: 0\n[Заявка принята автоматически]"
		bot.messages.send(chat_id=main_chat_id,message=send)
	else:
		for gpid in gp['items']:
			gnames+=str(gpid)+"," #Формируем список idшников групп
		gnames=bot.groups.getById(group_ids=gnames,fields="name") # Получаем названия групп
		ban_groups_desc="" # Сообщения на случай автоматического бана, см. строки ~130

		"""
		Дальше идёт сортировка групп. Если подходит по регулярке - отнять очки, если нет - добавить. Ну и так как
		ВК ограничивает кол-во символов в сообщении до ~4 тысяч, то если больше 4 - то оно отправляется и текст сбрасывается,
		чтобы отправить новое.
		"""

		for name in gnames:
			if re.search(pattern,name["name"]):
				if len(send)>=4000:
					bot.messages.send(message=send,chat_id=main_chat_id)
					send=""
				send+="\nFound "+name["name"]+" (http://vk.com/public"+str(name["id"])+")"
				if count<=5:
					ban_groups_desc+=name['name']+"; "
				pts-=cc
				count+=1
			else:
				pts+=1
		if ban_groups_desc!="": #Не очень по-питоновски, но не очень то важно, эта чтука обрезает список причины бана и добавляет в конец 'etc.'
			ban_groups_desc=ban_groups_desc[:-1]+" etc."
		send+=("\nPubs: "+str(gp["count"])) # Далее формируется итог
		send+=("\nCancer count: "+str(count))
		send+=("\nCancer percent: "+str(round((count/gp["count"])*100))+"%")
		send+=("\nCancer penalty: "+str(int(cc*count)))
		send+=("\nPTS: "+str(int(pts)))
		send+="\n=========\n[Yy]/[Nn]\n"
		if send!=None: # И если сообщение не пустрое..
			time.sleep(1)
			if count==0: #То при 0 паблов принимать автоматически
				bot.groups.approveRequest(group_id=GROUP_ID,user_id=user['id'])
				send+="[Заявка принята автоматически]\n"
				bot.messages.send(message=send,chat_id=main_chat_id)
				continue
			if count<=4: # Если менее 4 принимать автоматически
				bot.groups.approveRequest(group_id=GROUP_ID,user_id=user['id'])
				send+="[Заявка принята автоматически, 4 или меньше ракопаблов]\n"
				bot.messages.send(message=send,chat_id=main_chat_id)
				continue
			time.sleep(1)
			bot.messages.send(message=send,chat_id=main_chat_id) # Отправляем на растерзание админам
			c=0 #Это штука отвечает за время
			was=False #А эта за выход из цикла
			while was!=True:
				if c==60: #Если за минуту админы не решили, что делать, то выполняются следующие инструкции
					time.sleep(1)
					c=0 # Ну и счетчик обнуляется
					try:
						if pts<0: #Если очков меньше нуля, заявка отклоняется
							bot.groups.removeUser(group_id=GROUP_ID,user_id=user['id'])
							time.sleep(1)
							bot.messages.send(chat_id=main_chat_id,message="[Заявка отклонена автоматически]")
							if count>=20: #Если больше 20 паблов - следует бан
								bot.groups.banUser(group_id=GROUP_ID,user_id=user['id'],comment=ban_groups_desc,comment_visible=1)
								time.sleep(1)
								bot.messages.send(chat_id=main_chat_id,message="[Пользователь забанен: PTS<0 ; Больше 20 ракопаблов]")
						if pts>=0: # Если больше - принимается, если больше 0, но много ракопаблов - банит
							if (gp["count"]>=100 and round((count/gp["count"])*100)>=10) or (gp["count"]>=200 and round((count/gp["count"])*100)>=5):
								bot.groups.removeUser(group_id=GROUP_ID,user_id=user['id'])
								time.sleep(1)
								bot.groups.banUser(group_id=GROUP_ID,user_id=user['id'],comment=ban_groups_desc,comment_visible=1)
								bot.messages.send(chat_id=main_chat_id,message="[Заявка отклонена автоматически и пользователь забанен: PTS>=0 ; Процент больше 10]")
								continue
							bot.groups.approveRequest(group_id=GROUP_ID,user_id=user['id'])
							time.sleep(1)
							bot.messages.send(chat_id=main_chat_id,message="[Заявка принята автоматически]")
							continue
					except Exception as err: # Отловка чего-нибудь
						time.sleep(3)
						bot.messages.send(chat_id=main_chat_id,message=str(err))
					break
				time.sleep(1)
				c+=1
				ms=bot.messages.getHistory(chat_id=main_chat_id,count=1)['items'] #Смотрим последнее сообщение (при желании можете увеличить, должно работать)
				for message in ms:
					time.sleep(1)
					if not 'lid' in bot.storage.getKeys(): # Тут переменные с последним ответом на серверах ВК
						bot.storage.set(key='lid',value=0)
					else:
						lid=bot.storage.get(key='lid')
					if lid!=message["id"] or 'lid' not in globals(): #Проверка, не прошлый ли это ответ
						if re.match("\[[Yy]\]",message["body"]): #Если нет, то принять заяву, если соответствует ругулярке (Начинается с [y])
							was=True
							bot.storage.set(key='lid',value=message['id'])
							bot.groups.approveRequest(group_id=GROUP_ID,user_id=user['id'])
							bot.messages.send(chat_id=main_chat_id,message="[Заявка принята]")
							break
						if re.match("\[[Nn]\]",message["body"]): # То же самое, только отклонить
							waшкаs=True
							bot.storage.set(key='lid',value=message['id'])
							if  re.search(" -[bB]",message["body"]): # Ключ для [n], чтобы забанить ([n] -b)
								if  re.search(" -[bB] \".+\"",message["body"]): # [n] -b "Сюда можно влепить причину бана"
									b=re.search(" -[bB] \"(?P<comm>.+)\"",message["body"])
									bot.groups.banUser(group_id=GROUP_ID,user_id=user['id'],comment=b.group('comm') ,comment_visible=1)
									bot.messages.send(chat_id=main_chat_id,message="[Пользователь забанен, причина: \""+b.group('comm')+"\"]")
									time.sleep(0.5)
								else: #Или же она выбирается по пабликам
									bot.groups.banUser(group_id=GROUP_ID,user_id=user['id'],comment=ban_groups_desc,comment_visible=1)
									bot.messages.send(chat_id=main_chat_id,message="[Пользователь забанен]")
							bot.groups.removeUser(group_id=GROUP_ID,user_id=user['id'])
							bot.messages.send(chat_id=main_chat_id,message="[Заявка отклонена]")
							break
	time.sleep(1)

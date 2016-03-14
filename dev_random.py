# -*- coding: UTF-8 -*-
import random,time,re,os,json,requests,math
try:
	import vk
except:
	raise NameError("Vk module not found, use \'pip install vk\'")
from random import randint

TOKEN="" #тут токен
GROUP_ID=0 #тут айди группы
ARCHIVE_DIR="pics" #папка локального архива

class api: # Класс для вызова апи, который не даёт вызывать больше 3 раз в секунду
    def __init__(self, token):
        self.user = vk.API(access_token=token,session=vk.Session(),v=5.14) # вот тут подключение, версия 5.14 ибо новые ниоч
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
def main():

	suggested=bot.wall.get(owner_id=-GROUP_ID,filter="suggests",count=100,verify=False)

	"""
	Тут получаем записи из предложки, verify=False можете сменить,
	но у меня без него частенько вылетает с ошибкой проверки SSL
	"""

	if suggested["count"]>0:
		if suggested["count"]>100: #Костыль, чтобы получать из предложки больше сотни записей (не проверен)
			r=[]
			count_c=round(suggested["count"]/100)
			counting=0
			while counting<count_c:
				r.append(bot.wall.get(owner_id=-GROUP_ID,filter="suggests",verify=False,count=100,offset=100*count_c)["items"])
				counting+=1
			suggested=r[0][randint(0,len(r))]
		else:
			suggested=suggested["items"][randint(0,len(suggested["items"])-1)] #Соответственно тут получаем случайную
		if "attachments" in suggested: #Проверка на картинку, там у ВК их аж два, обычная и загруженная + гифку добавил на всякий случай
			if suggested["attachments"][0]["type"]=="photo" or suggested["attachments"][0]["type"]=="posted_photo" or suggested["attachments"][0]["type"]=="doc":
				if re.search("[Аа]нон(имно)*",suggested["text"]): #Проверка на анона по регулярке
					signed=0
					message=re.sub("[Аа]нон(имно)*", " ", suggested["text"]) # Срезаем саму надпись
				else:
					signed=1
					message=suggested["text"]
				bot.wall.post(owner_id=-GROUP_ID,post_id=suggested["id"],signed=signed,message=message) #Наконец, постим
			else:
				bot.wall.delete(owner_id=-GROUP_ID,post_id=suggested["id"]) # Если картинки нет - удалить из предложки
				main()
		else:
			bot.wall.delete(owner_id=-GROUP_ID,post_id=suggested["id"]) # ^
			main()
	else:
		pserver=bot.photos.getWallUploadServer(group_id=GROUP_ID) #Дальше загрузка картинки из архива
		pic = os.listdir(ARCHIVE_DIR)
		pic = pic[randint(0,len(pic)-1)]
		file = open(ARCHIVE_DIR+"/"+pic,'rb')
		photo = requests.post(pserver['upload_url'], files={'photo': file}) #Грузим
		photo = json.loads(photo.text)
		photo = bot.photos.saveWallPhoto(group_id=GROUP_ID,server=photo['server'],photo=photo['photo'],hash=photo['hash']) # И сохраняем
		photo='photo'+str(photo[0]['owner_id'])+"_"+str(photo[0]['id']) #Генерируем аттачмент
		bot.wall.post(owner_id=-GROUP_ID,attachments=photo,signed=1) # Постим
		file.close()
		os.system("rm \""+ARCHIVE_DIR+"/"+pic+"\"") #Чтобы не было повторов выпиливаем картинку
main()

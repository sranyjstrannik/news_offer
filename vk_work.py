import vk
import json
from PIL import Image
import requests
import time
import io

APP_ID = 5701604

def make_auth_session(login, password):
    session = vk.AuthSession(app_id=APP_ID, user_login=login, user_password=password, scope='audio,offline,video,wall,photos')
    api = vk.API(session)
    return api

def check_connection(api):
    good_answer = [{'first_name': 'Павел', 'last_name': 'Дуров', 'uid': 1}]
    check_answer = api.users.get(user_ids=1)
    return check_answer == good_answer

def get_audio(api):
    audiolist = api.audio.get(count=20)
    return audiolist


def get_video(api):
    videolist = api.video.get(count=10)
    return videolist[1:]


class MakeItAll:
    def __init__(self, login, password,waitingTime=None):
        self.api = make_auth_session(login, password)
        self.id = self.api.users.get()
        self.id = self.id[0]['uid']
        self.audiolist = get_audio(self.api)
        self.videolist = get_video(self.api)
        self.picturelist = []
        self.picturelist_preview = []
        # PIL images array
        # раньше было так
        self.videolist_preview = [Image.open(io.BytesIO(requests.get(v['image']).content)) for v in self.videolist]
        # теперь пока так
        self.videolist_preview = [v['title'] for v in self.videolist]
        self.audiolist_preview = [a['artist'] + ' - ' + a['title'] for a in self.audiolist]
        self.attachedV = []
        self.attachedA = []
        self.attachedP = []
        self.text = ''
        self.waitingTime = waitingTime
        self._attachements=""

        # проверяем, есть ли закрытый альбом вк с названием "temp"
        # если есть, прикрепленные фотки кидаем туда
        # если нет -- сперва создаем альбом

    def upload(self, groupid):
        attachments = ""
        # в self.videolist хранятся все доступные видео
        # в self.audiolist хранятся все доступные аудио
        # сперва формируем аудио
        for i in range(len(self.attachedA)):
            for a in self.audiolist:
                if a['artist'] + ' - ' + a['title'] == self.attachedA[i]:break
            attachments += ",audio"+str(a['owner_id'])+"_"+str(a["aid"])

        # теперь -- видео
        for i in range(len(self.attachedV)):
            for a in self.videolist:
                if a['title'] == self.attachedV[i]: break
            attachments += ",video"+str(a['owner_id'])+"_"+str(a["vid"])

        attachments+=self._attachements
        if attachments:
            if attachments[0]==',': attachments=attachments[1:]

        try:
            self.api.wall.post(owner_id="-"+str(groupid), message=self.text,attachments=attachments)
        except:
            print("Что-то пошло не так(")
        if self.waitingTime : time.sleep(self.waitingTime)

    def getID(self,grouplink):
        if ".com" in grouplink:
            grouplink = grouplink[grouplink.index('.com/')+5:]
            if 'public' in grouplink: grouplink=grouplink[6:]
        t=None
        try:
            t=self.api.groups.getById(group_id=grouplink)
            time.sleep(0.5)
        except:
            pass
        if t:
            return t[0]['name'],t[0]['gid']

    def createAlbumAndSaveTheLink(self):
        # получаем все альбомы текущего пользователя
        albms = self.api.photos.getAlbums()
        for al in albms:
            if al['title'] == "temp":
                self._albm = al['aid']
                return
        # создаём альбом temp
        albm = self.api.photos.createAlbum(privacy=3,title='temp')
        self._albm = albm['aid']

    def uploadPhoto(self,photopathArr):
        # получаем сервер для загрузки фото
        if not len(photopathArr): return
        srvr = self.api.photos.getUploadServer(album_id=self._albm)

        # получаем upload_url
        upload_url = srvr['upload_url']
        # делаем запрос на upload_url для загрузки фото
        data = dict()
        for i in range(0,len(photopathArr)):
            data.update({'file'+str(i+1) : open(photopathArr[i],'rb')})
        #получаем json
        answer = requests.post(url=upload_url,files=data)
        answer = json.loads(answer.text)
        jserver = answer["server"]
        jaid = answer["aid"]
        jhash = answer["hash"]
        jphotos_list = answer["photos_list"]#.decode('string_escape')
        #теперь делаем запрос на сохранение в альбоме
        t=self.api.photos.save(album_id=jaid,server=jserver,photos_list=jphotos_list,hash=jhash)
        self._attachements+=','+','.join([t['id'] for t in t])



from PyQt5 import uic,QtWidgets
from PyQt5.QtWidgets import  QFileDialog
from PyQt5.QtGui import QCursor,QImage,QPixmap
from PyQt5.QtCore import  QThread,pyqtSignal,pyqtSlot

import sys,time
from functools import partial
import vk_work

# простая формочка для выбора из предложенного списка
class Dial(QtWidgets.QDialog):
    finished = pyqtSignal(str)
    def __init__(self, textlist):
        super(Dial,self).__init__()
        uic.loadUi('listdialog.ui', self)
        for line in textlist:
            self.listWidget.addItem(line)
        self.listWidget.itemClicked.connect(self.itemclicked)
        self.accepted.connect(self.ok)
        self._item=""

    def itemclicked(self):
        self._item=self.listWidget.currentItem().text()

    def ok(self):
        self.finished.emit(self._item)
        self.close()

class WorkThread(QThread):
    name = pyqtSignal(str)

    def __init__(self,groups,maker,waitinTime=3):
        super(WorkThread,self).__init__()
        self.groups = groups
        self.maker = maker
        self.maker.waitingTime = waitinTime

        self.is_running = True
        self.pause = False
        self.waitinTime = waitinTime

    def run(self):
        self.maker.createAlbumAndSaveTheLink()
        for i in range(1 if len(self.maker.attachedP) <= 5 else 2):
            self.maker.uploadPhoto(self.maker.attachedP[i*5:(i+1)*5])
        while self.is_running:
            if self.pause:
                time.sleep(5)
                continue
            group = self.maker.getID(self.groups[0])
            try:
                self.name.emit(group[0]+" - /public"+str(group[1]))
                self.maker.upload(group[1])
            except: pass
            if len(self.groups)>1:
                self.groups = self.groups[1:]

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui,self).__init__()
        uic.loadUi('form.ui',self)

        self.maker = None
        self.trackCount = 0
        self.photoCount = 0
        self.videoCount = 0

        # массив кнопок и объектов для них
        self.trackButtons = [self.mButton_0,self.mButton_1,self.mButton_2,self.mButton_3,self.mButton_4,self.mButton_5,
                             self.mButton_6,self.mButton_7,self.mButton_8,self.mButton_9]
        self.tracks = [self.mlabel_0,self.mlabel_1,self.mlabel_2,self.mlabel_3,self.mlabel_4,self.mlabel_5,
                      self.mlabel_6,self.mlabel_7,self.mlabel_8,self.mlabel_9]
        self.photoButtons = [self.pbutton_0,self.pbutton_1,self.pbutton_2,self.pbutton_3,self.pbutton_4,self.pbutton_5,
                             self.pbutton_6,self.pbutton_7,self.pbutton_8,self.pbutton_9]
        self.photo = [self.plabel_0, self.plabel_1, self.plabel_2, self.plabel_3, self.plabel_4, self.plabel_5,
                       self.plabel_6, self.plabel_7, self.plabel_8, self.plabel_9]
        self.video = [self.vlabel_0, self.vlabel_1, self.vlabel_2, self.vlabel_3, self.vlabel_4, self.vlabel_5,
                       self.vlabel_6, self.vlabel_7, self.vlabel_8, self.vlabel_9]
        self.videoButtons = [self.vbutton_0,self.vbutton_1,self.vbutton_2,self.vbutton_3,self.vbutton_4,self.vbutton_5,
                             self.vbutton_6,self.vbutton_7,self.vbutton_8,self.vbutton_9]

        # скрываем их все
        for i in range(0,10):
            self.trackButtons[i].hide()
            self.videoButtons[i].hide()
            self.photoButtons[i].hide()
            self.tracks[i].hide()
            self.photo[i].hide()
            self.video[i].hide()

        # настройка внешнего вида
        self.label_4.setText('')
        # 0 -  экран с прогресс-баром
        #
        self.stackedWidget.setCurrentIndex(2)

        # настройка действия
        self.pushButton_2.clicked.connect(self.auth)
        self.pushButton_3.clicked.connect(lambda x:self.stackedWidget.setCurrentIndex(1))
        self.pushButton.clicked.connect(self.loadFromFile)
        # добавить аудио
        self.pushButton_6.clicked.connect(self.addTrack)
        # добавить видео
        self.pushButton_5.clicked.connect(self.addVideo)
        # добавить фото
        self.pushButton_4.clicked.connect(self.addPhoto)
        for i in range(0,10):
            # кнопки удаления аудио
            self.trackButtons[i].clicked.connect(partial(self.mdelete, i))
            # и видео
            self.videoButtons[i].clicked.connect(partial(self.vdelete, i))
            # и фото
            self.photoButtons[i].clicked.connect(partial(self.pdelete, i))
        # запуск
        self.pushButton_10.clicked.connect(self.go)
        # пауза
        self.pushButton_7.clicked.connect(self.pause)
        # остановить
        self.pushButton_8.clicked.connect(self.halt)

        self.show()

    # обработка удаления трека из прикрепленных
    def mdelete(self,i):
        self.trackCount -= 1
        self.tracks[self.trackCount].hide()
        self.trackButtons[self.trackCount].hide()
        # [0,1,2..i-1,i+1,..trackCount+1]
        arr = list(range(self.trackCount+1))
        arr.pop(i)
        for index,j in enumerate(arr):
            self.tracks[index].setText(self.tracks[j].text())

    # аналогичная обработка удаления видео
    def vdelete(self, i):
        self.videoCount -= 1
        self.video[self.videoCount].hide()
        self.videoButtons[self.videoCount].hide()
        arr = list(range(self.videoCount + 1))
        arr.pop(i)
        for index, j in enumerate(arr):
            self.video[index].setText(self.video[j].text())

    # и для фото
    def pdelete(self, i):
        self.photoCount -= 1
        # self.maker.picturelist хранит АДРЕСА фоток
        # self.maker.picturelist_preview хранит QPixmap'ы соответствующие
        self.photo[self.photoCount].hide()
        self.photoButtons[self.photoCount].hide()
        arr = list(range(self.photoCount+1))
        arr.pop(i)
        for index,j in enumerate(arr):
            self.maker.picturelist[index]=self.maker.picturelist[j]
            self.maker.picturelist_preview[index]=self.maker.picturelist_preview[j]
        for i in range(self.photoCount):
            self.photo[i].setPixmap(self.maker.picturelist_preview[i])

    # вспомогательная функция, нужная для прикрепления трека
    def mAddString(self,s):
        if not s: return
        self.tracks[self.trackCount].setText(s)
        self.tracks[self.trackCount].show()
        self.trackButtons[self.trackCount].show()
        self.trackCount += 1

    # ..и такая же, нужная для прикрепления видео
    def vAddString(self,s):
        if not s: return
        self.video[self.videoCount].setText(s)
        self.video[self.videoCount].show()
        self.videoButtons[self.videoCount].show()
        self.videoCount += 1

    # функция-обработчик процедуры прикрепления трека
    def addTrack(self):
        if self.trackCount+self.videoCount+self.photoCount != 10:
            self.d = Dial(self.maker.audiolist_preview)
            self.d.finished.connect(self.mAddString)
            self.d.show()

    # ..и процедуры добавления видео
    def addVideo(self):
        if self.trackCount+self.videoCount+self.photoCount != 10:
            self.d = Dial(self.maker.videolist_preview)
            self.d.finished.connect(self.vAddString)
            self.d.show()

    # ..ну и фото, само собой
    def addPhoto(self):
        if self.photoCount+self.videoCount+self.trackCount != 10:
            names = QFileDialog.getOpenFileNames(caption="Добавить фото",filter="Images (*.png *.xpm *.jpg)")[0]
            total = self.photoCount+self.videoCount+self.trackCount
            if len(names)+total>10: names = names[:10-total]
            # теперь нужно все эти фото добавить в массив и отобразить
            for i in range(self.photoCount, self.photoCount+len(names)):
                self.maker.picturelist_preview += [QPixmap(names[i-self.photoCount]).scaled(102,111)]
                self.maker.picturelist += [names[i-self.photoCount]]
                self.photo[i].setPixmap(self.maker.picturelist_preview[i])
                self.photo[i].show()
                self.photoButtons[i].show()

            self.photoCount += len(names)

    def loadFromFile(self):
        name,_ = QFileDialog.getOpenFileName()
        if name:
            try:
                f = open(name,'r')
                self.textEdit.setText(f.read())
            except:
                pass

    # аутентификация в приложении
    # если она прошла успешно, self.maker хранит экземпляр класса vk_work.MakeItAll
    def auth(self):
        login=self.lineEdit.text()
        password = self.lineEdit_2.text()

        try:
            self.maker = vk_work.MakeItAll(login,password)
            if vk_work.check_connection(self.maker.api):
                self.label_4.setStyleSheet("color:rgb(0, 170, 0);")
                self.label_4.setText('Успешно!')
                self.pushButton_3.setEnabled(True)
            else:
                self.label_4.setStyleSheet('color:rgb(170,0,0);')
                self.label_4.setText("Что-то пошло не так")
                self.pushButton_3.setEnabled(False)
        except:
            self.label_4.setStyleSheet('color:rgb(170,0,0);')
            self.label_4.setText("Что-то пошло не так")
            self.pushButton_3.setEnabled(False)

    def go(self):
        #сперва формируем нормальный список групп
        #groups = list(map(self.maker.getID, self.textEdit.toPlainText().split('\n')))
        groups = self.textEdit.toPlainText().split('\n')
        if not groups[-1]: groups=groups[:-1]
        if len(groups):
            self.maker.text = self.textEdit_2.toPlainText()
            self.maker.attachedA = [t.text() for t in self.tracks[:self.trackCount]]
            self.maker.attachedV = [t.text() for t in self.video[:self.videoCount]]
            self.maker.attachedP = self.maker.picturelist[:self.photoCount]
            self.maker._attachements = ""
            self.pushButton_7.setEnabled(True)
            self.stackedWidget.setCurrentIndex(0)
            self.label.setText("")
            # получили названия групп и их id
            # настраиваем progress-bar
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(len(groups))
            self.progressBar.setValue(0)
            wTime = 5
            try: wTime = int(self.lineEdit_3.text())
            except: pass
            self.wt = WorkThread(groups,self.maker,waitinTime=wTime)
            self.wt.name.connect(self.updateName)
            self.wt.start()
            self.pushButton_7.setText("Пауза")
            self.pushButton_8.setText("Остановить")

    def pause(self):
        self.wt.pause = not self.wt.pause
        self.pushButton_7.setText({"Пауза" : "Продолжить","Продолжить" : "Пауза"}[self.pushButton_7.text()])

    def updateName(self,s):
        self.label.setText(s)
        self.progressBar.setValue(self.progressBar.value()+1)
        if self.progressBar.value() == self.progressBar.maximum():
            self.wt.is_running = False
            self.wt.wait()
            self.label.setText("Задача завершена успешно!")
            self.pushButton_7.setEnabled(False)
            self.pushButton_8.setText("Новая задача")

    def halt(self):
        self.wt.is_running = False
        self.wt.wait()
        self.stackedWidget.setCurrentIndex(1)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    sys.exit(app.exec_())
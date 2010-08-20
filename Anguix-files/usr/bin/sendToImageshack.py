#!/usr/bin/env python
# -*- coding: utf-8 -*-

maximumHeight = 512 # maximum window height - window will grow with number of files, but will never pass this value
thumbnailSize = 96 #if image is not square ratio will be keeped
maxConnections = 2 # max number of concurrent uploads
showNotifications = True # True / False

#    Copyright (C) <2009>  <Sebastian Kacprzak> <naicik |at| gmail |dot| com>
#    Partial copyright <Balazs Nagy> <nxbalazs |at| gmail |dot| com> (few lines from his drop2imageshack plasma)

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Translated in Italian by Federico "Vecna" Vecchio
#                      email: fedevecchio |at| gmail |dot| com
#                     jabber: fedevecchio |at| jabber |dot| org
#


def importErrorDialog(txt):
    try: # try to show tkinker dialog
        import Tkinter
        master = Tkinter.Tk()
        w = Tkinter.Message(master, text=txt)
        w.pack()
        Tkinter.mainloop()
    except ImportError:
        from os import system
        zenityNotInstalled = system("command -v zenity")
        if not zenityNotInstalled: #sorry for double negation
            system("zenity --info --text='" + txt + "'")
        else:
            system("xterm -hold -geometry 150x1 -bg red -T '" + txt + "' -e true")
    import sys
    sys.exit()
try:
    import pygtk
    pygtk.require('2.0') # comboboxes needs pygtk 2.4 or higher, however they work fine with package 2.14.1-1ubuntu1 - probably version number differs..
    import gtk
except ImportError:
    importErrorDialog("Questo script richiede gtk e pygtk 2.0 o superiori")
except AssertionError:
    importErrorDialog("Questo script richiede pygtk 2.0 o superiori")
try:
    import pycurl
except ImportError:
    importErrorDialog("Questo script richiede pycurl. Installa il pacchetto python-pycurl.")
from StringIO import StringIO
from thread import start_new_thread
from threading import BoundedSemaphore, Lock
from gobject import GError
from xml.dom import minidom


acceptImageExtensions = ["jpg", "jpeg", "bmp", "gif", "png", "tif", "tiff"]
def correctExtension(file):
    return file.split('.')[-1].lower() in acceptImageExtensions

def copyToClipBoard(widget, text):
    display = gtk.gdk.display_manager_get().get_default_display()
    clipboard = gtk.Clipboard(display, "CLIPBOARD")#could be also "PRIMARY" for middle click paste
    clipboard.set_text(text)

def showDialog(parrent, description, title='Immagine caricata'):
        parrent.dialog = gtk.MessageDialog(
             parent         = None,
             flags          = gtk.DIALOG_DESTROY_WITH_PARENT,
             type           = gtk.MESSAGE_INFO,
             buttons        = gtk.BUTTONS_CLOSE,
             message_format = description
          )
        parrent.dialog.set_title(title)
        parrent.dialog.run()
        parrent.dialog.destroy()

class SendToImageshack():

    def __init__(self,mw,fileNumber):
        self.mw = mw
        self.fileNumber = fileNumber

    def progress(self, download_t, download_d, upload_t, upload_d):
	"""Callback function invoked when download/upload has progress."""
        prog = upload_d / upload_t
        try: # rather not needed
            gtk.gdk.threads_enter()
            self.mw.pbars[self.fileNumber].set_fraction(prog)
            if prog < 1:
                self.mw.pbars[self.fileNumber].set_text(str(upload_d) + " / " + str(upload_t))
            else:
                self.mw.pbars[self.fileNumber].set_text("Prego attendere")
        finally:
            gtk.gdk.threads_leave()


    def parseXML(self, xml):
        """parse given xml
        returns dictionary with keys: IM, Forum, Alt Forum, HTML, Direct, Forum Thumb, Alt Forum Thumb, HTML Thumb, Twitter Link"""
        print xml
        xmldoc = minidom.parse(StringIO(xml))
        
        links = {}
        imageLink = xmldoc.getElementsByTagName("image_link")[0].firstChild.data #xmldoc.childNodes[0].childNodes[1].firstChild.data
        thumbLink = xmldoc.getElementsByTagName("thumb_link")[0].firstChild.data #print xmldoc.childNodes[0].childNodes[3].firstChild.data
        adLink = xmldoc.getElementsByTagName("ad_link")[0].firstChild.data #print xmldoc.childNodes[0].childNodes[5].firstChild.data
        thumbExists = xmldoc.getElementsByTagName("thumb_exists")[0].firstChild.data #print xmldoc.childNodes[0].childNodes[7].firstChild.data
        links["Anteprima Immagine"] = adLink
        links["Forum"] = "[URL=" + adLink + "][IMG]"+ imageLink + "[/IMG][/URL]"
        links["Forum (2)"] = "[URL=" + adLink + "][IMG=" + imageLink + "][/IMG][/URL]"
        links["HTML"] = "<a target='_blank' href='" + adLink + "'><img src='" + imageLink + "' border='0'/></a>"
        links["Link Diretto"] = imageLink
        if thumbExists == "no":
            thumbLink = imageLink # thumb was not generated, use image as a thumb
        links["Forum Thumb"] = "[URL=" + adLink + "][IMG]"+ thumbLink + "[/IMG][/URL]"
        links["Forum Thumb (2)"] = "[URL=" + adLink + "][IMG=" + thumbLink + "][/IMG][/URL]"
        links["HTML Thumb"] = "'<a target='_blank' href='" + adLink + "'><img src='" + thumbLink + "' border='0'/></a>"
        links["Twitter Link"] =  "http://yfrog.com/?url=" + imageLink
        return links


    def upload(self, file, semaphore):
        if not correctExtension(file): # usually this check is not needed, but it can help later in other script
            showDialog(self.mw, "Estensione file non valida\nPuoi caricare solo "+ str(acceptImageExtensions), "Estensione file non valida")
            return
        curl = pycurl.Curl()

        curl.setopt(pycurl.URL, "http://www.imageshack.us/index.php")
        curl.setopt(pycurl.HTTPHEADER, ["Except:"])
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPPOST, [('fileupload', (pycurl.FORM_FILE, file)), ('xml', 'yes')])

        buf = StringIO()
        curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        curl.setopt(curl.NOPROGRESS, 0)
        curl.setopt(curl.PROGRESSFUNCTION, self.progress)

        semaphore.acquire()
        try:
            curl.perform()
        except pycurl.error:
            semaphore.release()
            self.showDialog(self.mw,
            """Upload non riuscito :(
Alcune possibili ragioni:
-errore durante il collegamento
-server scollegato
-la connessione è disattivata
-il server non accetta la tua immagine (grandi dimensioni, estensione sbagliata etc..)
-il server ha interrotto le comunicazioni per le troppe richieste

Si prega di provare più tardi. Se il problema persiste, caricare manualmente il file dal sito.""", "Upload non riuscito")
            return
        semaphore.release()
        
        if "504 Gateway Time-out" in buf.getvalue().strip(): self.upload(file, semaphore)
        else:
            links = self.parseXML(buf.getvalue().strip()) # sometimes there are leading witespace in stream and minidom don't like them
            self.mw.fileUploaded(self.fileNumber, links)


class MainWindow:
    pbars = []
    comboBoxes = []
    links = []
    uploadsCompleted = 0
    uploadsCompletedLock = Lock()
    linksNames = ['Anteprima Immagine', 'Forum', 'Forum (2)', 'HTML', 'Link Diretto', 'Forum Thumb', 'Forum Thumb (2)', 'HTML Thumb', 'Twitter Link']

    def destroy(self, widget, data=None):
        """Called before quiting"""
        gtk.main_quit()

    def windowClicked(self, widget, data=None):
        self.statusIcon.set_blinking(False)

    def fileUploaded(self, fileNumber, imageLinks):
        self.links[fileNumber] = imageLinks # there is one thread per file so this should be thread safe
        self.uploadsCompletedLock.acquire()
        try: #rather not needed
            self.uploadsCompleted += 1
        finally:
            self.uploadsCompletedLock.release()        
        try:
            gtk.gdk.threads_enter()
            self.pbars[fileNumber].set_text("Upload completato")
            self.comboBoxes[fileNumber].show()
            self.statusIcon.set_tooltip("Caricati " + str(self.uploadsCompleted) + " di " + str(len(self.comboBoxes)) + " file.")
            if(self.uploadsCompleted == len(self.comboBoxes)):
                self.statusIcon.set_blinking(True)
                if showNotifications:
                    try:
                        import pynotify
                        if pynotify.init("Carica su Imageshack"):
                            notification = pynotify.Notification("Tutti i file sono stati caricati.","Seleziona il link dal menù a tendina o dalla systray per copiarlo in memoria","go-up")
                            notification.show()
                    except ImportError: pass
        finally:
            gtk.gdk.threads_leave()


    def copyAllLinks(self, widget, linkType=None):
        if not linkType:
            linkType = self.linksNames[widget.get_active()]
        allLinks = ''
        for link in self.links:
            if link:
                allLinks += link[linkType]  + "\n" # to lazy for .join ;p
        copyToClipBoard(None, allLinks)

    def copyLink(self, widget, fileNumber, linkType=-1):
        #copyToClipBoard(None, self.links[fileNumber][widget.get_active()])
        if linkType < 0: # 0 also give false
            linkType = widget.get_active() #get selected combo box item
        copyToClipBoard(None, self.links[fileNumber][self.linksNames[linkType]])
        self.pbars[fileNumber].set_text("Copiato in memoria") #somehow don't want to work with gtk lock, but works without it, no thread read from pbars so that shouldn't be important
        

    def statusIconClicked(self, icon):
        if not self.window.is_active():
            self.window.present()
        else:
            self.window.hide()
        self.statusIcon.set_blinking(False)

    def createStatusIconMenu(self,correctFiles):
        self.menu = gtk.Menu()
        fileNumber = 0
        for file in correctFiles:
            sm = gtk.Menu()
            menuItem = gtk.MenuItem(file.split('/')[-1])
            menuItem.set_submenu(sm)
            self.menu.append(menuItem)

            linkNumber = 0
            for name in self.linksNames:
                menuItem = gtk.MenuItem(name)
                menuItem.connect("activate", self.copyLink, fileNumber, linkNumber)
                sm.append(menuItem)
                linkNumber += 1
            fileNumber += 1

        if len(correctFiles) > 1:
            self.menu.append(gtk.MenuItem()) #separator
            sm = gtk.Menu()
            menuItem = gtk.MenuItem('All')
            menuItem.set_submenu(sm)
            self.menu.append(menuItem)

            linkNumber = 0
            for name in self.linksNames:
                menuItem = gtk.MenuItem(name)
                menuItem.connect("activate", self.copyAllLinks, linkNumber)
                sm.append(menuItem)
                linkNumber += 1

        self.menu.append(gtk.MenuItem()) #separator
        menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        menuItem.connect('activate', self.destroy, self.statusIcon)
        self.menu.append(menuItem)

        self.statusIcon.connect('popup-menu', self.statusIconMenu, self.menu)

    def statusIconMenu(self,widget,button,time,menu=None):
        self.statusIcon.set_blinking(False)
        if button == 3:
            if menu:
                menu.show_all()
                menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusIcon)


    def createCombobox(self):
        comboBox = gtk.combo_box_new_text()
        for name in self.linksNames:
            comboBox.append_text(name)
        return comboBox


    def addFiles(self, files, vbox):
        """adds progressbar, buttons and image for each file to GUI. Returns list of files with correct extension"""
        correctFiles = []
        for file in files:
            if not correctExtension(file):
                showDialog(self, "Estensione non valida per il file: " + file + "\nPuoi caricare soltanto "+ str(acceptImageExtensions) + "\nIl file non verrà caricato.", "Estensione non valida")
                continue

            hbox = gtk.HBox(False, 0)
            vbox.pack_start(hbox, False, False, 0)
            hbox.show()

            vboxSmall = gtk.VBox(False, 0)
            hbox.pack_start(vboxSmall, False, False, 0)
            vboxSmall.show()

            label = gtk.Label(file.split('/')[-1])
            vboxSmall.pack_start(label, False, False, 0)
            label.show()

            pbar = gtk.ProgressBar()
            self.pbars.append(pbar)
            vboxSmall.pack_start(pbar, False, False, 0)
            pbar.show()

            comboBox = self.createCombobox()
            self.links.append([])
            comboBox.connect("changed", self.copyLink, len(correctFiles))
            comboBox.connect("notify::popup-shown", self.windowClicked)
            comboBox.show()#"show" comboboxes to make windows size calculation precise(comboboxes will be hidden again before window will be desplayed)
            self.comboBoxes.append(comboBox)

            vboxSmall.pack_start(comboBox, False, False, 0)

            image = gtk.Image()
            original_pixbuf = gtk.gdk.pixbuf_new_from_file(file)
            ratio = float(original_pixbuf.get_width()) / original_pixbuf.get_height()
            thumbnailSizeX = thumbnailSize
            thumbnailSizeY = thumbnailSize
            if ratio > 1:
                thumbnailSizeY /= ratio
            else:
                thumbnailSizeX *= ratio
            pixbuf_zoomed = original_pixbuf.scale_simple(int(thumbnailSizeX), int(thumbnailSizeY), gtk.gdk.INTERP_BILINEAR)
            image.set_from_pixbuf(pixbuf_zoomed)
            hbox.pack_start(image, False, False, 8)
            image.show()

            separator = gtk.HSeparator()
            vbox.pack_start(separator, False, False, 4)
            separator.show()

            correctFiles.append(file)

        if not correctFiles:
            import sys
            sys.exit()
        return correctFiles

    def setWindowSize(self, vboxMainSize):
        windowSize = self.window.size_request()
        width = windowSize[0]
        if width < vboxMainSize[0]:
            width = vboxMainSize[0]
        heigh = vboxMainSize[1] + 8#error margin;)
        if maximumHeight < heigh:
            heigh = maximumHeight

        self.window.set_size_request(width+4,heigh)

    def __init__(self,files):
        self.statusIcon = gtk.StatusIcon()
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_resizable(True)

        self.window.connect("destroy", self.destroy)
        self.window.set_title("Carica su Imageshack")
        self.window.set_border_width(0)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.window.add(scroll)
        scroll.show()

        align = gtk.Alignment(0.5, 0.0, 0, 0)
        scroll.add_with_viewport(align)
        align.show()

        vboxMain = gtk.VBox(False, 0)
        align.add(vboxMain)
        vboxMain.show()

        correctFiles = self.addFiles(files, vboxMain)

        self.statusIcon.set_tooltip("Caricamento di " + str(len(self.comboBoxes)) + " file.")

        align = gtk.Alignment(0.5, 0.5, 0, 0)
        vboxMain.pack_start(align, False, False, 0)
        align.show()

        hbox = gtk.HBox(False, 5)
        hbox.set_border_width(10)
        align.add(hbox)
        hbox.show()

        if len(correctFiles) > 1:
            vbox = gtk.VBox(False, 0)
            hbox.pack_start(vbox, False, False, 0)

            vbox.show()
            label = gtk.Label("Tutti i file:")
            vbox.pack_start(label,False, False, 0)
            label.show()
            comboBox = self.createCombobox()
            comboBox.connect("changed", self.copyAllLinks)
            comboBox.connect("notify::popup-shown", self.windowClicked)
            vbox.pack_start(comboBox, False, False, 0)
            comboBox.show()

        button = gtk.Button("Chiudi")
        button.connect("clicked", self.destroy)
        hbox.pack_start(button, False, False, 2)
        button.show()
        
        self.createStatusIconMenu(correctFiles)
        self.setWindowSize(vboxMain.size_request())
        for combo in self.comboBoxes: #hide comboboxes, they will be displayed when links are ready
            combo.hide()

        self.window.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.window.connect("button-press-event", self.windowClicked)
        self.window.show()

        i = 0
        semaphore = BoundedSemaphore(maxConnections)
        for file in correctFiles:
            sti = SendToImageshack(self,i)
            i += 1
            start_new_thread(sti.upload, (file,semaphore))


def uploadFiles(files):
    """sends files given by paths, separated by new lines"""
    gtk.gdk.threads_init()
    mw = MainWindow(files)

    icon_theme = gtk.icon_theme_get_default()
    try:
        pixbuf = icon_theme.load_icon("go-up", 24, 0)
        mw.statusIcon.set_from_pixbuf(pixbuf)
        mw.statusIcon.connect('activate', mw.statusIconClicked)
        mw.statusIcon.set_visible(True)
        mw.window.set_icon(pixbuf)
    except GError, exc:
        print "Impossibile caricare l'icona nella traybar", exc # non fatal, we lose only tray icon
    gtk.main()

if __name__ == "__main__":
    from sys import argv
    if len(argv) >1:
        args = argv[1:] #firs argment is file name, so ignore it
        uploadFiles(args)

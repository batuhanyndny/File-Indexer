from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview
import shelve
import os
import mimetypes
import re
import time
from itertools import cycle

class DosyaArayici(Tk):

    def __init__(self):
        super(DosyaArayici, self).__init__()
        self.pathIndexed = False
        self.indexedFiles = []
        # results = { fileName: {"wordScore" : Number, "lModScore": Number}}
        self.results = {}
        self.searchFilter = {
            "code": ["text/javascript", "application/javascript", "text/css", "text/x-python", "text/x-c", "text/x-java-source", "java", "application/java-vm", "text/html"],
            "text": ["application/rtf", "text/plain"]
        }
        self.paginationIndices = (0, 10)

        # UI settings
        self.title("YAZ104")
        self.geometry("900x700+300+100")
        self.configure(background="grey")
        self.grid_columnconfigure(0, weight=1)

        # UI vars
        self.mPadding = 65
        self.pageNumber = StringVar()
        self.directory = StringVar()
        self.searchDepth = StringVar()
        self.searchBar = StringVar()
        self.weight1 = StringVar()
        self.weight2 = StringVar()
        self.wordCb = IntVar()
        self.lmodCb = IntVar()
        self.passedTime = StringVar()
        self.numOfFiles = StringVar()
        self.font = ("Courier", 15)

        # First label
        Label(self, text="Dosya Arayıcı", font=("Courier", 20), bg="grey").grid(row=0, column=0)

        # Seperator
        Frame(self, bg="black", height=5, width=700).grid(row=1, column=0, sticky="EW")

        # Path
        self.ui_path = Frame(self, background="grey")
        self.ui_path.grid(row=2, column=0, sticky="W", padx=50)

        Label(self.ui_path, text="Başlangıç Dizini:", bg="grey", font=self.font).grid(row=0, column=0, sticky="NW", pady=8)
        self.directory.set("path/to/search") 
        
        self.directory.trace_add("write", self.UI_pathChange)
        Entry(self.ui_path, width=30, fg="black", textvariable=self.directory).grid(row=0, column=2, padx=70, pady=5)

        # Depth
        self.ui_depth = Frame(self.ui_path, background="grey")
        self.ui_depth.grid(row=1, column=0, sticky="w")

        Label(self.ui_depth, text="Derinlik:", bg="grey", font=self.font).grid(row=0, column=0, sticky="SW", pady=5)
        self.searchDepth.set("1")
        Entry(self.ui_depth, width=3, fg="black", textvariable=self.searchDepth).grid(row=0, column=1)

        # Create indices
        Button(self.ui_path, text="İndex Oluştur", command=self.UI_indexOlustur, highlightbackground='#3E4149').grid(row=1, column=2, padx=70, pady=5)

        # Seperator
        Frame(self, bg="black", height=5, width=700).grid(row=3, column=0, sticky="EW")

        # Main Body
        self.searchBar.set("kelime1 kelime2 kelime3")
        Entry(self, width=30, fg="black", textvariable=self.searchBar).grid(row=4, column=0, padx=self.mPadding, pady=10, sticky="W")

        # Filtreler framei
        self.filters = Frame(self, background="grey")
        self.filters.grid(row=5, column=0, padx=self.mPadding, pady=5, sticky="NWE")
        self.filters.grid_columnconfigure(0, weight=1)
        self.filters.grid_columnconfigure(1, weight=1)
        self.filters.grid_columnconfigure(2, weight=1)
        self.filters.grid_columnconfigure(3, weight=1)

        Label(self.filters, text="Sıralama kriteri", bg="grey", font=self.font).grid(row=0, column=0, sticky='NW')
        Label(self.filters, text="Ağırlıklar", bg="grey", font=self.font).grid(row=0, column=1, sticky='N')
        Label(self.filters, text="Filtre", bg="grey", font=self.font).grid(row=0, column=2, sticky='N')

        # Sorting filters
        self.wordCb.set(False)
        self.lmodCb.set(False)
        Checkbutton(self.filters, text="Kelime uzaklığı", background="grey", fg="black", font=self.font, variable=self.wordCb, onvalue=1, offvalue=0, height=2).grid(row=1, column=0, sticky="w")
        Checkbutton(self.filters, text="Erişim zamanı", background="grey", fg="black", font=self.font, variable=self.lmodCb, onvalue=1, offvalue=0, height=2).grid(row=2, column=0, sticky="w")

        # Weights
        self.weight1.set("1")
        self.weight2.set("1")
        Entry(self.filters, width=3, fg="black", textvariable=self.weight1).grid(row=1, column=1)
        Entry(self.filters, width=3, fg="black", textvariable=self.weight2).grid(row=2, column=1)

        # ListBox for filters
        self.listBox = Listbox(self.filters, selectmode=MULTIPLE, bg="#e3e3e3", fg="black", width=13, height=3)
        self.listBox.insert(0, "Düz metin")
        self.listBox.insert(1, "Program kodu")
        self.listBox.selection_clear(0, END)
        self.listBox.selection_set(0, 1)
        self.listBox.grid(row=1, column=2)

        # Search button
        Button(self.filters, text="Ara", command=self.UI_search, highlightbackground='#3E4149', width=9).grid(row=1, column=3)

        # List and pagination
        self.files = Frame(self, background="grey")
        self.files.grid(row=6, column=0)

        # search time
        self.passedTime.set("Süre: 0")
        self.numOfFiles.set("Dosya sayısı: 0")
        Label(self.files, textvariable=self.passedTime, bg="grey", font=self.font).grid(row=0, column=0, sticky='NE')
        Label(self.files, textvariable=self.numOfFiles, bg="grey", font=self.font).grid(row=0, column=0, sticky='NW')

        # treeView
        self.resultView = Treeview(self.files, height=14)
        self.resultView["columns"] = ("Path", "size", "word score", "lmod score")
        self.resultView.column("#0", width=30, minwidth=30, stretch=YES, anchor=W)
        self.resultView.column("Path", width=600, minwidth=550, stretch=NO, anchor=W)
        self.resultView.column("size", width=40, minwidth=35, stretch=NO, anchor=W)
        self.resultView.column("word score", width=80, minwidth=80, stretch=NO, anchor=E)
        self.resultView.column("lmod score", width=80, minwidth=80, stretch=NO, anchor=E)

        self.resultView.heading("#0", text="#", anchor=W)
        self.resultView.heading("Path", text="Mutlak patika", anchor=W)
        self.resultView.heading("size", text="Boyut", anchor=W)
        self.resultView.heading("word score", text="Kelime Puani", anchor=W)
        self.resultView.heading("lmod score", text="Erişim Puani", anchor=W)

        self.resultView.grid(row=1, column=0)

        self.pagination = Frame(self.files, background="grey")
        self.pagination.grid(row=2, column=0, sticky="ES", pady=5)

        self.pageNumber.set("1")

        Label(self.pagination, text="Sayfa:", bg="grey", font=self.font).grid(row=0, column=0, padx=2)
        Entry(self.pagination, width=5, font=self.font, fg="black", textvariable=self.pageNumber, state='readonly', justify=CENTER).grid(row=0, column=2, padx=2)

        self.pageDown = Button(self.pagination, text="Önceki", highlightbackground='#3E4149', command=self.UI_pageDown, state=DISABLED, width=5, height=2)
        self.pageDown.grid(row=0, column=1, padx=2)

        self.pageUp = Button(self.pagination, text="Sonraki", highlightbackground='#3E4149', command=self.UI_pageUp, state=DISABLED, width=5, height=2)
        self.pageUp.grid(row=0, column=3, padx=2)

        # init
        self.createTables()
        self.searcher = Searcher(self.words, self.files)

    def __del__(self):
        self.close()

    def close(self):
        if hasattr(self, 'content'):
            self.words.close()

    # --------------------
    # CRAWLER
    # --------------------

    # shelve veritabanı oluşturma
    def createTables(self):
        # files = {path: fileContent}
        self.files = shelve.open('files.db', writeback=True, flag='n')
        # words = {
        #     word: [
        #         {path : [indices] }, 
        #         {path2: [indices2] } 
        #     ],
        #     word2: [
        #         {path3 : [indices3] }, 
        #         {path2: [indices4] } 
        #     ]
        # }
        self.words = shelve.open('words.db', writeback=True, flag='n')

    # filtreleri almak
    def getSelectedFilters(self):
        selection = self.listBox.curselection()
        sFilter = []
        for i in selection:
            if i == 0:
                for i in self.searchFilter["text"]:
                    sFilter.append(i)
            if i == 1:
                for i in self.searchFilter["code"]:
                    sFilter.append(i)
        return sFilter

    # dosya indexli mi
    def isIndexed(self, file):
        if file in self.indexedFiles:
            with open(file, "r") as f:
                content = f.read()
                f.close()
                if content != self.files[file]:
                    return False
            return True
        else:
            return False

    # İndexlenmemiş dosyayı veri tabanına kaydetme
    def indexFile(self, file, path):
        fullPath = path + os.path.sep + file
        if self.isIndexed(fullPath):
            print("Skipping ", file, ", Already indexed")
            return False

        print("INDEXING: ", file)

        with open(fullPath, "r") as f:
            try:
                # read content
                content = f.read()
            except UnicodeDecodeError:
                messagebox.showwarning("Decode hatası", "{} dosyası okunamadı".format(fullPath))
                return False
            # update files db
            self.files.update({ fullPath: content})
            # split content to words
            splitted = content.split()
            for word in splitted:
                # calculate indices
                indices = [i for i, x in enumerate(splitted) if x == word]
                # update index dict
                if word in self.words.keys():
                    new = { fullPath: indices }
                    if new not in self.words[word]:
                        self.words[word].append(new)
                else:
                    self.words.update({ word: [ {fullPath: indices} ]})
            self.indexedFiles.append(fullPath)
            f.close()
        return True

    # os.walk() metodunun herhangi bir depth parametresi var mı diye araştırırken buldum.
    # Sorunumu tam olarak çözdüğü için kullanmak istedim.
    # kaynak: https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
    def walklevel(self, some_dir, level=1):
        some_dir = some_dir.rstrip(os.path.sep)
        try:
            assert os.path.isdir(some_dir)
        except AssertionError:
            messagebox.showerror("Patika Hatası", "Belirtilen patika bulunamadı")
        num_sep = some_dir.count(os.path.sep)
        for root, dirs, files in os.walk(some_dir):
            yield root, dirs, files
            num_sep_this = root.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]

    # Dosyaları tarayan ana fonksiyon
    def fileIndexer(self):
        self.words.clear()
        targetDir = self.directory.get()
        numOfIndexedFiles = 0
        try:
            depth = int(self.searchDepth.get())
        except Exception:
            messagebox.showerror("Hata", "Lütfen derinlik için bir tamsayı girin")
            return

        for path, dirs, files in self.walklevel(targetDir, depth):
            for file in files:
                f = self.indexFile(file, path)
                if f:
                    numOfIndexedFiles += 1
        
        self.pathIndexed = True
        messagebox.showinfo("tamamlandı", "İndexleme tamamlandı. {} dosya indexlendi".format(numOfIndexedFiles))

    # --------------------
    # UI FONKSİYONLARI
    # --------------------
    def UI_indexOlustur(self):
        self.fileIndexer()

    # Girdi olan ağırlıkları alan fonksiyon
    def getWeights(self):
        try:
            w1 = int(self.weight1.get())
        except Exception:
            w1 = None

        try:
            w2 = int(self.weight2.get())
        except Exception:
            w2 = None

        return (w1, w2)

    # TreeView'i gğncelleyen fonksiyon
    def ui_insert_resultView(self):
        # resultView'i temizle
        self.resultView.delete(*self.resultView.get_children())
        # sıralama ölçütlerini al
        wordOrd = self.wordCb.get()
        lmodOrd = self.lmodCb.get()
        ind = 1
        # indexleri al
        pInd1, pInd2 = self.paginationIndices
        # sıralama ölçeklerine göre sırala
        # (Her iki ölçüt de seçildiğinde kararsız davranıyor)
        if wordOrd and lmodOrd:
            sort = sorted(self.results, key=lambda x: (self.results[x]['word'], self.results[x]['lmod']), reverse=True)
            for path in sort[pInd1:pInd2]:
                size = os.stat(path).st_size
                self.resultView.insert("", ind, text=str(ind + pInd1), values=(path, size, self.results[path]['word'], str(self.results[path]['lmod'])[0:5]))
                ind += 1
        elif wordOrd:
            sort = sorted(self.results, key=lambda x: (self.results[x]['word']), reverse=True)
            for path in sort[pInd1:pInd2]:
                size = os.stat(path).st_size
                self.resultView.insert("", ind, text=str(ind + pInd1), values=(path, size, self.results[path]['word'], str(self.results[path]['lmod'])[0:5]))
                ind += 1
        elif lmodOrd:
            sort = sorted(self.results, key=lambda x: (self.results[x]['lmod']), reverse=True)
            for path in sort[pInd1:pInd2]:
                size = os.stat(path).st_size
                self.resultView.insert("", ind, text=str(ind + pInd1), values=(path, size, self.results[path]['word'], str(self.results[path]['lmod'])[0:5]))
                ind += 1

    #
    def UI_search(self):
        start = time.time()
        # path girilmiş mi
        if self.pathIndexed:
            # bir sıralama ölçütü seçilmiş mi
            wordOrd = self.wordCb.get()
            lmodOrd = self.lmodCb.get()
            if wordOrd or lmodOrd:
                w1, w2 = self.getWeights()
                # her iki siralama olcutu secilmis mi secilmisse weightler girilmis mi
                if self.wordCb.get() and self.lmodCb.get() and not w1 and not w2:
                    messagebox.showerror("Hata", "En az 1 sayısal değerde agırlık girin")
                    return
                # Kategori secimini kontrol et
                FILTERS = self.getSelectedFilters()
                if len(FILTERS) <= 0:
                    messagebox.showerror("Hata", "En az 1 dosya kategorisi seçin")
                    return
                else:
                    # search kelimesini al
                    q = self.searchBar.get()
                    if len(q) <= 0:
                        messagebox.showwarning("Hata", "Aramak istediğiniz kelimeyi girin")
                        return
                    # " isaretine gore inputu ayarla
                    if '"' in q:
                        q = q.split('"')
                        q = [w.strip() for w in q if len(w) > 0]
                    else:
                        q = q.split()
                    # ayarlanan inputu searcher'a gonder
                    self.results = self.searcher.query(q, FILTERS, (w1, w2))
                    # sonuclari degerlendir
                    if self.results:
                        self.ui_insert_resultView()
                        if len(self.results.keys()) > 10:
                            self.pageUp.config(state=NORMAL)
                        else:
                            self.pageUp.config(state=DISABLED)
                        end = time.time()
                        c = end - start
                        minutes = c // 60 % 60
                        seconds = c % 60
                        self.numOfFiles.set("Dosya sayisi: " + str(len(self.results.keys())))
                        self.passedTime.set("Sure: {}".format(minutes + (seconds / 100)))
                        print("Sure: {}".format(minutes + (seconds / 100)))
                    else:
                        messagebox.showwarning("Uyarı", "Aradığınız kelimeler bulunamadı")
                        return
            else:
                messagebox.showerror("Hata", "Bir siralama olcutu belirtin")
                return
        else:
            messagebox.showerror("Hata", "Önce indexleme yapmak zorundasınız")
            return

    # Path enrtybox değiştiği zaman indexleme zorunluluğu getir.
    def UI_pathChange(self, mode, a, c):
        self.pathIndexed = False

    # pagination için buton fonksiyonları
    def UI_pageUp(self):
        maxInd = len(self.results)
        print(maxInd)
        ind1, ind2 = self.paginationIndices
        ind1 += 10
        ind2 += 10
        print(ind2)
        if ind2 >= maxInd:
            ind2 = maxInd
            self.pageUp.config(state=DISABLED)
            print("DISABLED")
        self.paginationIndices = (ind1, ind2)
        self.pageDown.config(state=NORMAL)
        self.pageNumber.set(str(int(self.pageNumber.get()) + 1))
        self.ui_insert_resultView()

    def UI_pageDown(self):
        minInd = 0
        ind1, ind2 = self.paginationIndices
        ind1 -= 10
        ind2 -= 10
        if ind1 <= minInd:
            ind1 = minInd
            self.pageDown.config(state=DISABLED)
        if ind2 < 10:
            ind2 = 10
        self.paginationIndices = (ind1, ind2)
        self.pageUp.config(state=NORMAL)
        self.pageNumber.set(str(int(self.pageNumber.get()) - 1))
        self.ui_insert_resultView()

# --------------------
# Searcher Classı
# --------------------
class Searcher:

    def __init__(self, content, files):
        #
        # words = {
        #     word: [
        #         {path : [indices] }, 
        #         {path2: [indices2] } 
        #     ],
        #     word2: [
        #         {path3 : [indices3] }, 
        #         {path2: [indices4] } 
        #     ]
        # }
        #
        self.words = content
        # files = {path: fileContent}
        self.files = files
        # scorelari gecici olarak tutmak icin dict
        # scores = { path: { 'lmod': score, 'word': score4 }, path2: { 'lmod': score2, 'word': score3 } }
        self.scores = {}
        # arama kelimeleri
        self.searchWords = []

    # 2 kelime arasındaki kelimeleri saymak için contenti bölen fonksiyon
    def splitter(self, indices, content):
        parts = []
        lastInd = 0
        indices.sort(key=lambda x: x[0])
        for i, j in indices:
            parts.append(content[lastInd:i].strip())
            parts.append(content[i:j].strip())
            lastInd = j
        parts.append(content[lastInd:].strip())
        return parts

    def calcWordDistance(self, indices): 
        # indexleri karsilikli olarak pair yapip min score hesapla
        generalScore = 0

        def zipper(A, B):
            # kaynak: https://stackoverflow.com/questions/19686533/how-to-zip-two-differently-sized-lists/19686624
            return list(zip(A, cycle(B)) if len(A) > len(B) else zip(cycle(A), B))

        for i in range(len(indices)):
            arr1 = indices[i]
            try:
                arr2 = indices[i + 1]
            except IndexError:
                break
            possIndices = zipper(arr1, arr2)
            minScore = float('inf')
            for i, j in possIndices:
                score = abs(i - j)
                if score < minScore:
                    minScore = score
            generalScore += minScore

        return generalScore

    # Dosyayanın erişim zamanını hesaplayan fonksiyon
    def calcLastModified(self, path):
        lastModified = os.stat(path).st_mtime
        now = time.time()
        days = (now - lastModified) // 86400
        hours = (now - lastModified) // 3600 % 24
        minutes = (now - lastModified) // 60 % 60

        score = days + (hours / 10) + (minutes / 100)
        return score

    # 2 kelime arasındaki kelimeleri sayan fonksiyon
    def calculateScores(self, results, weights):
        # Eski skor dict sil
        self.scores.clear()
        # normalize icin min ve max degerler
        wordMinscore = float('inf')
        lmodMinscore = float('inf')
        
        for path, wordIndices in results.items():
            # lmod score
            lmodScore = self.calcLastModified(path)
            # create node
            self.scores[path] = {}
            # edit dict
            self.scores[path]['lmod'] = lmodScore
            lmodMinscore = min(lmodMinscore, lmodScore)
            # word score
            if len(self.searchWords) > 1:
                # get values
                indices = list(wordIndices.values())
                # calc score
                wordScore = self.calcWordDistance(indices)
                # edit dict
                self.scores[path]['word'] = wordScore
                wordMinscore = min(wordMinscore, wordScore)
            else:
                self.scores[path]['word'] = 0
        # normalize scores
        for path, i in results.items():
            self.normalizescores(weights, wordMinscore, lmodMinscore, self.scores[path])

    # normalize fonksiyonu
    def normalizescores(self, weights, wordMinscore, lmodMinscore, scoreDict):
        vsmall = 0.001  # Avoid division by zero errors 
        # weightleri al
        wordW, lmodW = weights
        for scoreType, value in scoreDict.items():
            if scoreType == 'word':
                if wordW:
                    score = (float(wordMinscore * wordW) / max(vsmall, value))
                    scoreDict[scoreType] = score if score < 1 else 1
                else:
                    scoreDict[scoreType] = float(wordMinscore) / max(vsmall, value)
                
            elif scoreType == 'lmod':
                if lmodW:
                    score = (float(lmodMinscore * lmodW) / max(vsmall, value)) 
                    scoreDict[scoreType] = score if score < 1 else 1
                else:
                    scoreDict[scoreType] = float(lmodMinscore) / max(vsmall, value)
            else:
                raise Exception("Logic error")

    # regular expressions ile input kelimelerini arayan fonksiyon
    def wordFinder(self, FILTERS):
        for sWord in self.searchWords:
            if " " in sWord:
                firstWord = sWord.split()[0]
                try:
                    wordDetail = self.words[firstWord]
                except KeyError:
                    yield None
                for pathAndIndices in wordDetail:
                    path = list(pathAndIndices.keys())[0]
                    mimeType = mimetypes.guess_type(path)[0]
                    if mimeType in FILTERS:
                        matches = [f.span() for f in re.finditer(r'\b({0})\b'.format(sWord), self.files[path], flags=re.IGNORECASE)]
                        if matches:
                            parts = self.splitter(matches, self.files[path])
                            ind = 0
                            returnWordAndIndices = {sWord: []}
                            for i in range(len(parts)):
                                if parts[i] != sWord:
                                    ind += len(parts[i].split())
                                else:
                                    returnWordAndIndices[sWord].append(ind)
                            yield path, returnWordAndIndices
                    else:
                        continue
            else:
                try:
                    wordDetail = self.words[sWord]
                    returnWordAndIndices = []
                    for detail in wordDetail:
                        for path, indices in detail.items():
                            mimeType = mimetypes.guess_type(path)[0]
                            if mimeType in FILTERS:
                                yield path, { sWord: indices }
                            
                except KeyError:
                    yield None

    # turn yileding values to dict
    def getWordIndices(self, FILTERS):
        try:
            retDict = {}
            for path, wordsAndIndices in self.wordFinder(FILTERS):
                if path in retDict.keys():
                    retDict[path].update(wordsAndIndices)
                else:
                    retDict[path] = wordsAndIndices
            return retDict
        except TypeError:
            return None

    # Searcher ana fonksiyonu.
    def query(self, words, FILTERS, weights):
        # Aranacak kelimeler
        self.searchWords = words
        # arama sounclari
        results = self.getWordIndices(FILTERS)
        # kelime bulunamadi ise False dondur
        if not results:
            return False
        # skorlama
        self.calculateScores(results, weights)
        if self.scores:
            return self.scores
        else:
            return False


# Main
if __name__ == '__main__':
    dosyaArayici = DosyaArayici()
    dosyaArayici.mainloop()

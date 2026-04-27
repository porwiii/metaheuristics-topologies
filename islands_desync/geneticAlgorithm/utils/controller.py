from islands_desync.geneticAlgorithm.utils import fileslister
import os


class Controller:
    def __init__(self, katalog, wyspa, czy_kom):
        self.czy_kom = czy_kom
        if self.czy_kom:
            print("rusza controller")

        os.makedirs(katalog, exist_ok=True)

        self.ctrlFile = open(
            os.path.join(katalog, f"kontrolW{wyspa}Start.ctrl.txt"),
            "a",
        )
        self.ctrlFile.close()
        self.katalog = katalog

    def endOfProcess(self, wyspa, co):
        os.makedirs(self.katalog, exist_ok=True)

        self.ctrlFile = open(
            os.path.join(self.katalog, f"kontrolW{wyspa}End.ctrl.txt"),
            "w",
        )
        self.ctrlFile.write(str(co))
        self.ctrlFile.close()

    def endOfWholeProbe(self, proba):
        print("KAT", self.katalog)
        parent = os.path.dirname(self.katalog)

        os.makedirs(parent, exist_ok=True)

        self.ctrlFile = open(
            os.path.join(parent, f"seriaEnd{proba}.txt"),
            "a",
        )
        self.ctrlFile.close()


    def isEndComplete(self, ilewysp):
        fl = fileslister.FilesLister
        ilePlikow = fl.countFilesExtensionLike(fl, self.katalog, "End.ctrl.txt")
        if ilePlikow == ilewysp:
            return True
        else:
            return False

    def isCtrlComplete(self, ilewysp):
        fl = fileslister.FilesLister
        ilePlikow = fl.countFilesExtensionLike(fl, self.katalog, "Start.ctrl.txt")
        if ilePlikow == ilewysp:
            return True
        else:
            return False

    def __str__(self):
        return "controller"

    def __del__(self):
        if self.czy_kom:
            print("koniec controller")

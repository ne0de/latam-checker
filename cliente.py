import socket, psutil, os, sys, hashlib, atexit, subprocess
from threading import Thread

FORBIDDEN_EXTENSIONS = ['.ini', '.cs', '.asi', '.cleo', '.sf']
FORBIDDEN_PROCESSES = ['aimbot.exe', 'proccesshacker.exe', 'resourcehacker.exe', 'tcpview.exe', 'notepad.exe']

CHECKSUMS = {
    'bass.dll': '3F04620D6627ABE5C3B4747FAF26603AB7A006C81B2021AB4689BDD7033BB4CD',
    'eax.dll': 'B2DA4F1E47EF8054C8390EAD0B97D1FBB0C547245B79B8861CFA92CE9EF153FB',
    'gta_sa': 'FC09D6FD20CA721BF5A533F3DA8AC8515AD1D7C6263F4761EB4267F7A7F7C725',
    'ogg.dll': '4A4F65427E016B3C5AE0D2517A69DB5F1CDC7A43D2C0A7957E8DA5D6F378F063',
    'samp.dll': '15DB80C5C9E02E011F16509D081D1CE7C8526238200814EBC16BA1F4F9FF12AB',
    'stream.ini': 'E5B4AC3E7797A271660A091BDC0E4663BEEDCAB43ACAEE2473086CA8F925A148',
    'vorbis.dll': 'FEFDA850B69E007FCEBA644483C7616BC07E9F177FC634FB74E114F0D15B0DB0',
    'vorbisFile.dll': 'A08923479000CEC366967FB8259E0920B7AA18859722C7DDA1415726BED4774F', #6CCF42587CAEEE3A09F6372A4E73CC657EA67C7FDC0234017A39ADAAC6D7BC80
    'vosbisHooked.dll': 'A08923479000CEC366967FB8259E0920B7AA18859722C7DDA1415726BED4774F',
    'samp.exe': '6837B2AA93CAE4AF073A12207B502C6705F43C3B1A9F642E3FA4EB4D5C351555',
    'AntTweakBar.dll': '8A34A705489A9A9457E6232CB27D518C7ED51C86740DF91BC61888F52BF91845'
}

class Client(Thread):
    def __init__(self):
        super().__init__()
        self.__running = False
        self.__socket = socket.socket()
    
    def connect(self, host, port):
        print(f'Enlazando con el servidor {host}:{port} ..')
        self.updateDir()
        if not self.gta_path or not self.samp_path:
            print("Tienes que tener abierto GTA y SAMP")
            return
        try:
            self.__socket.connect((host, port))
            data = self.__socket.recv(2048).decode('utf-8')
            if(data == "NO"):
                print("Error: primero tienes que estar conectado en el servidor desde samp.")
                input('Presiona una tecla para salir.')
                return
            if(data == "OK"):
                print("Conexion establecida!")
                self.__socket.send(str.encode(f'h-{self.gethash()}'))
                data = self.__socket.recv(2048).decode('utf-8')
                if(data == "NO"): self.dis()
                self.__socket.send(str.encode(f'i-{self.GetUUID()}'))
                if(data == "NO"): self.dis()
                self.start()
        except socket.error as e:
            print(e)
            print("Error: no se pudo enlazar con ese servidor.")
            input('Presiona una tecla para salir.')

    def checkExtensions(self, listext, path):
        l = []
        for _, _, filenames in os.walk(path):
            for filename in filenames:
                if filename == "stream.ini": continue
                if any(ext in filename for ext in listext):
                    l.append(filename)
        return l

    def checkHash(self, checksums, path):
        fm = {}
        for _, _, filenames in os.walk(path):
            for filename in filenames:
                if filename in checksums.keys():
                    with open(path + '/' + filename, 'rb') as f:
                        sha256 = hashlib.sha256()
                        while True:
                            chunk = f.read(16 * 1024)
                            if not chunk:
                                break
                            sha256.update(chunk)
                        if filename == "vorbisFile.dll" and sha256.hexdigest().upper() == "6CCF42587CAEEE3A09F6372A4E73CC657EA67C7FDC0234017A39ADAAC6D7BC80":
                            pass
                        elif not sha256.hexdigest().upper() == checksums[filename]: fm[filename] = sha256.hexdigest().upper()
        return fm
    
    def checkProccesses(self, list):
        fp = []
        for process in psutil.process_iter():
            if process.name().lower() in list: 
                fp.append(process)
        return fp

    def processPath(self, processname):
        for proc in psutil.process_iter():
            if proc.name().lower() == processname:
                path = proc.cwd()
                return path
        return False

    def updateDir(self):
        self.gta_path = self.processPath('gta_sa.exe')
        self.samp_path = self.processPath('samp.exe')
    
    def GetUUID(self):
        cmd = 'wmic csproduct get uuid'
        uuid = str(subprocess.check_output(cmd))
        pos1 = uuid.find("\\n")+2
        uuid = uuid[pos1:-15]
        return uuid

    def dis(self):
        print('Te has desconectado')
        self.__socket.close()

    def gethash(self):
        hash = ""
        with open(sys.argv[0], 'rb') as f:
            sha256 = hashlib.sha256()
            while True:
                chunk = f.read(16 * 1024)
                if not chunk:
                    break
                sha256.update(chunk)
            hash = sha256.hexdigest().upper()
        return hash

    def run(self):
        while True:
            self.updateDir()

            fe = self.checkExtensions(FORBIDDEN_EXTENSIONS,self.samp_path)
            if bool(fe):
                self.__socket.send(str.encode(f"d-Contiene modificadores (cs, asi, entre otros)"))
                data = self.__socket.recv(2048).decode('utf-8')
                if(data == "NO"): break

            lp = self.checkProccesses(FORBIDDEN_PROCESSES)
            if bool(lp):
                nl = []
                for p in lp: nl.append(p.name())
                self.__socket.send(str.encode(f"d-Proceso sospechoso: {','.join(nl)}"))
                data = self.__socket.recv(2048).decode('utf-8')
                if(data == "NO"): break
            
            if self.gta_path != self.samp_path:
                self.__socket.send(str.encode('d-Directorios distintos (samp - gta)'))
                data = self.__socket.recv(2048).decode('utf-8')
                if(data == "NO"): break

            hl = self.checkHash(CHECKSUMS, self.samp_path)
            if bool(hl):
                print(hl)
                nhl = []
                for f in hl.keys(): nhl.append(f)
                self.__socket.send(str.encode(f"d-Archivos modificados: {','.join(nhl)}"))
                data = self.__socket.recv(2048).decode('utf-8')
                if(data == "NO"): break
            
        self.dis()
        return

if __name__ == "__main__":
    print("-- LATAM CHECKER - BETA ANTICHEAT --")
    host = str(input('IP: '))
    port = int(input('PUERTO: '))
    client = Client()
    client.connect(host, port)

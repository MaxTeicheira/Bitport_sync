# from operator import truediv
from os import name
import paramiko
import os.path
from stat import S_ISDIR
from paramiko import file
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    AdaptiveETA, FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, \
    SimpleProgress, Timer, UnknownLength



class sftp_downloader():

    def __init__(self, remotePath, localPath, username, password, skipVideos=False) -> None:
        super().__init__()
        self.host = "sftp.bitport.io"
        self.port = 2022
        self.transport = paramiko.Transport((self.host, self.port))
        #Create a Transport object

        self.skipVideos = skipVideos
        self.localPath = localPath
        self.password = password
        self.username = username
        self.transport.connect(username = self.username, password = self.password)
        #Connect to a Transport server
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        #Create an SFTP client

        self.widgets = ['Downloading: ', Percentage(), ' ',
                        Bar(marker='#',left='[',right=']'),
                        ' ', ETA(), ' ', FileTransferSpeed(), ' ', Counter()]
        #Progress bar inits

    def sftp_walk(self, remotepath):
        # Kindof a stripped down  version of os.walk, implemented for 
        # sftp.  Tried running it flat without the yields, but it really
        # chokes on big directories.
        path=remotepath
        files=[]
        folders=[]
        for f in self.sftp.listdir_attr(remotepath):
            if S_ISDIR(f.st_mode):
                folders.append(f.filename)
            else:
                files.append(f.filename)
        # print (path,folders,files)
        yield path,folders,files
        for folder in folders:
            new_path=os.path.join(remotepath,folder)
            for x in self.sftp_walk(new_path):
                yield x



    def display(self, in_bytes, total_bytes):
        self.bar.update(in_bytes)
    ##Was experimenting with display as class to persist the progressbar object

    def does_file_exist_and_finished(self, remotepath, filename, remote_size):
        full_path = os.path.join(self.localPath, remotepath,filename)
        # print(full_path)
        try:
            self.local_size = os.path.getsize(full_path)
        except:
            self.local_size = 0
        if filename[-3:] in ["mp4", "mkv"] and self.skipVideos:
                print("Skipping b/c large video file")
                self.printer(remotepath, filename, remote_size)
                return True
        if os.path.exists(full_path):
            print("File exists")
            self.printer(remotepath, filename, remote_size)
            if self.local_size >= remote_size:
                # print(filename[-3:])
                print("File fully downloaded")
                return True
        else:
            print("File does not exist")
            self.printer(remotepath, filename, remote_size)
        return False

    def printer(self, remotepath, filename, remote_size):
        full_path = os.path.join(remotepath,filename)
        print(filename)
        print("Local file size: ", self.local_size)
        print("Remote file size: " + str(remote_size))
        print("Filetype: " + filename[-3:])
    


    def get_all(self, remotepath,localpath):
            #  recursively download a full directory
            #  Harder than it sounded at first, since paramiko won't walk
            #
            # For the record, something like this would gennerally be faster:
            # ssh user@host 'tar -cz /source/folder' | tar -xz

            self.sftp.chdir(os.path.split(remotepath)[0])
            parent=os.path.split(remotepath)[1]
            try:
                os.mkdir(localpath)
            except:
                pass
            for walker in self.sftp_walk(parent):
                try:
                    os.mkdir(os.path.join(localpath,walker[0]))
                except:
                    pass
                for file in walker[2]:
                    self.current_file_path_and_name = self.sftp.stat(os.path.join(walker[0],file))
                    print("\n\n")
                    print('*'*80)
                    if not self.does_file_exist_and_finished(walker[0], file, self.current_file_path_and_name.st_size):
                        self.bar = ProgressBar( widgets=self.widgets, max_value=self.current_file_path_and_name.st_size)
                        self.bar.start()
                        self.sftp.get(os.path.join(walker[0],file),os.path.join(localpath,walker[0],file),callback=self.display)
                        self.bar.finish()
                    # else:
                    #     print("Already Downloaded")
                        





remotePath = "/"
localPath = "/Users/maxteicheira/Downloads/Bitport"
username = "max.teicheira@gmail.com"
password = "smashy1"
conn = sftp_downloader(remotePath, localPath, username, password, skipVideos=True)

conn.get_all(remotePath, localPath)

conn.sftp.close()
conn.transport.close()
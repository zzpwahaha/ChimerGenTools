# created by mark brown
from traceback import print_tb
import h5py as h5
from colorama import Fore, Style
from numpy import array as arr
import numpy as np
import Miscellaneous as misc
import datetime
import pandas as pd
from tqdm import tqdm
dataAddress = None
currentVersion = 1

def annotate(fileID=None, expFile_version=currentVersion, useBaseA=True):
    #hashNum = int(input("Title-Level: "))
    hashNum = 3
    #titleStr = ''.join('#' for _ in range(hashNum)) + ' ' + title
    with ExpFile(expFile_version=expFile_version) as file:
        print('annotating file ' + str(fileID));
        file.open_hdf5(fileID, openFlag='a', useBase=useBaseA)
        if checkAnnotation(fileID, force=False, expFile_version=expFile_version):        
            title, notes, num = getAnnotation(fileID, expFile_version=expFile_version, useBaseA=useBaseA)
            title = input("Run Title (\"q\" to Quit) (prev was \""+title+"\"):")
            if title == 'q':
                raise RuntimeError("Annotation Quit")
            notes = input("Experiment Notes (\"q\" to Quit)(prev was \""+notes+"\"):")
            if notes == 'q':
                raise RuntimeError("Annotation Quit")
        else:
            title = input("Run Title (\"q\" to Quit):")
            if title == 'q':
                raise RuntimeError("Annotation Quit")
            notes = input("Experiment Notes (\"q\" to Quit):")
            if notes == 'q':
                raise RuntimeError("Annotation Quit")

        if 'Experiment_Notes' in file.f['Miscellaneous'].keys():
            del file.f['Miscellaneous']['Experiment_Notes']
        dset2 = file.f['Miscellaneous'].create_dataset("Experiment_Notes", shape=(1,), dtype="S"+str(len(notes))) 
        dset2[0] = np.string_(notes)
        
        if 'Experiment_Title' in file.f['Miscellaneous'].keys():
            del file.f['Miscellaneous']['Experiment_Title']
        dset3 = file.f['Miscellaneous'].create_dataset("Experiment_Title", shape=(1,), dtype="S"+str(len(title))) 
        dset3[0] = np.string_(title)
        
        if 'Experiment_Title_Level' in file.f['Miscellaneous'].keys():
            del file.f['Miscellaneous']['Experiment_Title_Level']
        dset4 = file.f['Miscellaneous'].create_dataset("Experiment_Title_Level", shape=(1,), dtype="i8") 
        dset4[0] = hashNum

        
def checkAnnotation(fileNum, force=True, quiet=False, expFile_version=currentVersion):
    try:
        with ExpFile(fileNum, expFile_version=expFile_version) as f:
            if (   'Experiment_Notes' not in f.f['Miscellaneous']
                or 'Experiment_Title' not in f.f['Miscellaneous']):
                #pass
                if force:
                    raise RuntimeError('HDF5 File number ' + str(fileNum) + ' Has not been annotated. Please call exp.annotate() to annotate the file.')
                else:
                    print('HDF5 File number ' + str(fileNum) + ' Has not been annotated. Please call exp.annotate() to annotate the file.')
                return False
    except OSError:
        # failed to open file probably, nothing to annotate.
        return False
    except KeyError:
        # file failed to open, probably a special run
        return False
    return True


def getAnnotation(fid, expFile_version=currentVersion, useBaseA=True):
    with ExpFile() as f:
        f.open_hdf5(fid, useBase=useBaseA)
        f_misc = f.f['Miscellaneous']
        if (   'Experiment_Notes' not in f_misc
            or 'Experiment_Title' not in f_misc):
            raise RuntimeError('HDF5 File number ' + str(fid) + ' Has not been annotated. Please call exp.annotate() to annotate the file.')
        if 'Experiment_Title_Level' not in f_misc:
            expTitleLevel = 0
        else:
            expTitleLevel = f_misc['Experiment_Title_Level'][0]
        return (f_misc['Experiment_Title'][0].decode("utf-8"), 
                f_misc['Experiment_Notes'][0].decode("utf-8"),
                expTitleLevel)
    
def getConfiguration(fid, expFile_version=currentVersion, useBaseA=True):
    with ExpFile() as file:
        file.open_hdf5(fid, useBase=useBaseA)
        f_MI = file.f['Master-Input']
        if ('Configuration' not in f_MI):
            return ""
        return ''.join([char.decode('utf-8') for char in f_MI['Configuration']])
    
#"J:\\Data repository\\New Data Repository"
def setPath(day, month, year, repoAddress="\\\\jilafile.colorado.edu\\scratch\\regal\\common\\LabData\\NewRb\\CryoData"):
    """
    This function sets the location of where all of the data files are stored. It is occasionally called more
    than once in a notebook if the user needs to work past midnight.

    :param day: A number string, e.g. '11'.
    :param month: The name of a month, e.g. 'November' (must match file path capitalization).
    :param year: A number string, e.g. '2017'.
    :return:
    """
    global dataAddress
    if type(day) == int:
        day = str(day)
    if type(year) == int:
        year = str(year)
    dataAddress = repoAddress + "\\" + year + "\\" + month + "\\" + month + " " + day + "\\Raw Data\\"
    #print("Setting new data address:" + dataAddress)
    return dataAddress


def addNote(fileID=None):
    notes = input("New Experiment Note:")
    with ExpFile() as file:
        noteNum = 1
        file.open_hdf5(fileID, openFlag='a')
        while noteNum < 1000:
            if 'Experiment_Note_' + str(noteNum) not in file.f['Miscellaneous'].keys():
                dset2 = file.f['Miscellaneous'].create_dataset("Experiment_Note_" + str(noteNum), shape=(1,), dtype="S"+str(len(notes))) 
                dset2[0] = np.string_(notes)
                break
            else:
                noteNum += 1

def getStartDatetime(fileID):
    with ExpFile() as file:
        file.open_hdf5(fileID)
        file.exp_start_date, file.exp_start_time, file.exp_stop_date, file.exp_stop_time = file.get_experiment_time_and_date()
        dt = datetime.datetime.strptime(file.exp_start_date + " " + file.exp_start_time[:-1], '%Y-%m-%d %H:%M:%S')
    return dt
                 
# Exp is short for experiment here.
class ExpFile:
    """
    a wrapper around an hdf5 file for easier handling and management.
    """
    def __init__(self, file_id=None, expFile_version=currentVersion, useBaseA=True, keyParameter=None):
        """
        if you give the constructor a file_id, it will automatically fill the relevant member variables.
        """
        if expFile_version is None:
            expFile_version = currentVersion
        #print('expfile version:', expFile_version)
        # copy the current value of the address
        self.version = expFile_version
        self.f = None
        self.key_name = None
        self.key = None 
        self.pics = None
        self.pixis_pics = None
        self.reps = None
        self.exp_start_time = None
        self.exp_start_date = None
        self.exp_stop_time = None
        self.exp_stop_date = None
        self.data_addr = dataAddress
        self.file_id = file_id
        if file_id is not None:
            self.f = self.open_hdf5(fileID=file_id, useBase=useBaseA)
            self.key_name, self.key = self.get_key(keyParameter=keyParameter)
            self.pics = self.get_pics()
            self.reps = self.get_reps()
            self.exp_start_date, self.exp_start_time, self.exp_stop_date, self.exp_stop_time = self.get_experiment_time_and_date()
            self.rep_first = self.f['./Master-Runtime/Repetitions-First'][0]
            # try:
            #     self.pixis_pics = self.get_pixis_pics()
            # except FileNotFoundError:
            #     print(r'Did not find Pixis file PixisData_{:d}.txt, make sure it is named with the same id as the h5 file.'.format(file_id)
            #      + ' Or you can call get_pixis_pics mannually with the correct data id')
    
    def __enter__(self):
        return self

    
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return self.f.close()
        except AttributeError:
            return
            
    
    def open_hdf5(self, fileID=None, useBase=True, openFlag='r'):      
        
        if type(fileID) == int:
            path = self.data_addr + "data_" + str(fileID) + ".h5"
        elif useBase:
            # assume a file address itself
            path = self.data_addr + fileID + ".h5"
        else:
            path = fileID
        try:
            file = h5.File(path, openFlag)            
        except OSError as err:
            raise OSError("Failed to open file! file address was \"" + path + "\". OSError: " + str(err))
        self.f = file
        return file
    
    def get_reps(self):
        # call this one.
        self.reps = self.f['Master-Runtime']['Repetitions'][0]
        return self.reps      

    def get_params(self):
        return self.f['Master-Runtime']['Parameters'] 
    
    def get_key(self, keyParameter=None):
        """
        :param file:
        :return:
        """
        keyNames = []
        keyValues = []
        foundOne = False
        nokeyreturn = 'No-Variation', arr([1])
        try:
            params = self.get_params()
            for var in params:
                if not params[var]['Is Constant'][0]:
                    foundOne = True
                    keyNames.append(''.join([char.decode('utf-8') for char in params[var]['Name']]))
                    keyValues.append(arr(params[var]['Key Values']))

            if foundOne:
                if len(keyNames) > 1:
                    return keyNames, arr(misc.transpose(arr(keyValues)))
                else:
                    return keyNames[0], arr(keyValues[0])
            else:
                if keyParameter is None:
                    return nokeyreturn
                else:
                    for var in params:
                        name = ''.join([char.decode('utf-8') for char in params[var]['Name']])
                        print(name)
                        if name == keyParameter:
                            return name , arr(params[var]['Key Values'])
                    return "Key not found!", arr([1])
        except KeyError:
            return nokeyreturn
        
    def get_pics(self):
        p_t = arr(self.f['Andor']['Pictures'])
        pics = p_t.reshape((p_t.shape[0], p_t.shape[2], p_t.shape[1]))
        return pics
    
    def get_pixis_pics(self, file_id=None):
        file_id = file_id or self.file_id
        print("Getting files from {:s}PixisData_{:d}.txt".format(self.data_addr,file_id))
        d = pd.read_csv("{:s}PixisData_{:d}.txt".format(self.data_addr,file_id), sep='\t', header=None)
        _pixi_datas = []
        pixi_data = []
        for index, row in tqdm(d.iterrows()):
            if row.item() != ';':
                pixi_data.append([int(num) for num in row.item().split(' ') if num])
                if index==len(d.index)-1:
                    _pixi_datas.append(np.array(pixi_data))
            else:
                _pixi_datas.append(np.array(pixi_data))
                pixi_data = []
        pixi_datas = np.array(_pixi_datas)
        if self.rep_first:
            # pixi_datas = np.array(pixi_datas).reshape(ee.key.size, ee.get_reps())
            pixi_datas = np.array(pixi_datas).reshape([self.key.size, self.get_reps(),*pixi_datas.shape[1:]])
            # pixi_datas = np.array(pixi_datas).reshape([ee.key.size,1000,*pixi_datas.shape[1:]])
            print("Repetition First, data shape ", pixi_datas.shape)
        else:
            pixi_datas = np.array(pixi_datas).reshape([self.get_reps(), self.key.shape[0],*pixi_datas.shape[1:]])
            pixi_datas = np.einsum('ijkl->jikl',pixi_datas) #np.transpose(pixi_datas,(1,0,2,3)).shape # both should work
            print("Variation First, data shape ", pixi_datas.shape)
        self.pixis_pics = pixi_datas
        return pixi_datas


    def get_mako1_pics(self):
        p_t = arr(self.f['Mako']['Mako1']['Pictures'])
        pics = p_t.reshape((p_t.shape[0], p_t.shape[2], p_t.shape[1]))
        return pics
    
    def get_mako2_pics(self):
        p_t = arr(self.f['Mako']['Mako2']['Pictures'])
        pics = p_t.reshape((p_t.shape[0], p_t.shape[2], p_t.shape[1]))
        return pics

    def get_basler_pics(self):
        p_t = arr(self.f['Basler']['Pictures'])
        pics = p_t.reshape((p_t.shape[0], p_t.shape[2], p_t.shape[1]))
        return pics
        
    def get_avg_pic(self):
        pics = self.get_pics()
        avg_pic = np.zeros(pics[0].shape)
        for p in pics:
            avg_pic += p
        avg_pic /= len(pics)
        return avg_pic

    def get_avg_mako1_pic(self):
        pics = self.get_mako1_pics()
        avg_pic = np.zeros(pics[0].shape)
        for p in pics:
            avg_pic += p
        avg_pic /= len(pics)
        return avg_pic

    def get_avg_mako2_pic(self):
        pics = self.get_mako2_pics()
        avg_pic = np.zeros(pics[0].shape)
        for p in pics:
            avg_pic += p
        avg_pic /= len(pics)
        return avg_pic

    def get_avg_basler_pic(self):
        pics = self.get_basler_pics()
        avg_pic = np.zeros(pics[0].shape)
        for p in pics:
            avg_pic += p
        avg_pic /= len(pics)
        return avg_pic
        
    def get_binning(self, type):
        if type == 'andor':
            binH = self.f['Andor']['Image-Dimensions']['Horizontal-Binning'][()][0]
            binV = self.f['Andor']['Image-Dimensions']['Vertical-Binning'][()][0]
        elif type == 'mako1':
            binH = self.f['Mako']['Mako1']['Image-Dimensions']['Horizontal-Binning'][()][0]
            binV = self.f['Mako']['Mako1']['Image-Dimensions']['Vertical-Binning'][()][0]
        elif type == 'mako2':
            binH = self.f['Mako']['Mako2']['Image-Dimensions']['Horizontal-Binning'][()][0]
            binV = self.f['Mako']['Mako2']['Image-Dimensions']['Vertical-Binning'][()][0]
        else:
            raise ValueError('Bad value for CameraType.')
        return binH, binV 

    def print_all(self):
        self.__print_hdf5_obj(self.f,'')
    
    def print_all_groups(self):
        self.__print_groups(self.f,'')

        
    def print_parameters(self):
        self.__print_hdf5_obj(self.get_params(),'')
        
    def __print_groups(self, obj, prefix):
        """
        Used recursively to print the structure of the file.
        obj can be a single file or a group or dataset within.
        """
        for o in obj:
            if o == 'Functions':
                print(prefix, o)
                self.print_functions(prefix=prefix+'\t')
            elif o == 'Master-Script' or o == "Seq. 1 NIAWG-Script":
                print(prefix,o)
            elif type(obj[o]) == h5._hl.group.Group:
                print(prefix, o)
                self.__print_groups(obj[o], prefix + '\t')
            elif type(obj[o]) == h5._hl.dataset.Dataset:
                print(prefix, o)
            #else:
            #    raise TypeError('???')
        
    def __print_hdf5_obj(self, obj, prefix):
        """
        Used recursively in other print functions.
        obj can be a single file or a group or dataset within.
        """
        for o in obj:
            if o == 'Functions':
                print(prefix, o)
                self.print_functions(prefix=prefix+'\t')
            elif o == 'Master-Script' or o == "Seq. 1 NIAWG-Script":
                print(prefix,o)
                self.print_script(obj[o])
            elif type(obj[o]) == h5._hl.group.Group:
                print(prefix, o)
                self.__print_hdf5_obj(obj[o], prefix + '\t')
            elif type(obj[o]) == h5._hl.dataset.Dataset:
                print(prefix, o, ':',end='')
                self.__print_ds(obj[o],prefix+'\t')
            else:
                raise TypeError('???')
    
    def print_functions(self, brief=True, prefix='', which=None):
        """
        print the list of all functions which were created at the time of the experiment.
        if not brief, print the contents of every function.
        """
        funcList = self.f['Master-Input']['Functions']
        for func in funcList:
            if which is not None:
                if func != which:
                    print(func)
                    continue
            print(prefix,'-',func,end='')
            if not brief:
                print(': \n---------------------------------------')
                # I think it's a bug that this is nested like this.
                indvFunc = funcList[func]
                for x in indvFunc:
                    for y in indvFunc[x]:
                        # print(Style.DIM, y.decode('utf-8'), end='') for some reason the 
                        # DIM isn't working at the moment on the data analysis comp...
                        print(y.decode('utf-8'), end='')
                print('\n---------------------------------------\ncount=')
            print('')

    def print_master_script(self):
        # A shortcut
        self.print_script(self.f['Master-Input']['Master-Script'])

    def print_niawg_script(self):
        # A shortcut
        self.print_script(self.f['NIAWG']['Seq. 1 NIAWG-Script'])

        
    def print_script(self, script):
        """
        special formatting used for printing long scripts which are stored as normal numpy bytes.
        """
        print(Fore.GREEN,'\n--------------------------------------------')
        for x in script:
            print(x.decode('UTF-8'),end='')
        print('\n--------------------------------------------\n\n', Style.RESET_ALL)
            
    def __print_ds(self, ds, prefix):
        """
        Print dataset
        """
        if type(ds) != h5._hl.dataset.Dataset:
            raise TypeError('Tried to print non dataset as dataset.')
        else:
            if len(ds) > 0:
                if type(ds[0]) == np.bytes_:
                    print(' "',end='')
                    for x in ds:
                        print(x.decode('UTF-8'),end='')
                    print(' "',end='')
                elif type(ds[0]) in [np.uint8, np.uint16, np.uint32, np.uint64, 
                                     np.int8, np.int16, np.int32, np.int64, 
                                     np.float32, np.float64]:
                    for x in ds:
                        print(x,end=' ')
                else:
                    print(' type:', type(ds[0]), ds[0])
            print('')
            
    def get_pic_info(self):
        infoStr = 'Number of Pictures: ' + str(self.pics.shape[0]) + '; '
        infoStr += 'Picture Dimensions: ' + str(self.pics.shape[1]) + ' x ' + str(self.pics.shape[2]) + '\n'
        return infoStr
    
        
    def get_basic_info(self):
        """
        Some quick easy to read summary info
        """
        infoStr = self.get_pic_info()
        
        infoStr += 'Variations: ' + str(len(self.key)) + ";\t"
        infoStr += 'Repetitions: ' + str(self.reps) + ';\tExp File Version: ' + str(self.version) + ';'"\n"
        infoStr += 'Experiment started at (H:M:S) ' + str(self.exp_start_time) + ' on (Y-M-D) ' + str(self.exp_start_date) + ', '
        infoStr += 'And ended at ' + str(self.exp_stop_time) + ' on ' + str(self.exp_stop_date) + "\n"
        if 'Experiment_Notes' in self.f['Miscellaneous'].keys():
            infoStr += 'Experiment Notes: ' + str(self.f['Miscellaneous']['Experiment_Notes'][0].decode("utf-8")) +"\n"
        else:
            infoStr += "Experiment Notes: HDF5 NOT ANNOTATED: please call exp.Annotate() to annotate this file.\n"
        if 'Experiment_Rationale' in self.f['Miscellaneous'].keys():
            infoStr += '(Old Notes format:) Experiment Rationale: ' + str(self.f['Miscellaneous']['Experiment_Rationale'][0].decode("utf-8")) + "\n"
        if 'Experiment_Result' in self.f['Miscellaneous'].keys():
            infoStr += '(Old Notes format:) Experiment Result: ' + str(self.f['Miscellaneous']['Experiment_Result'][0].decode("utf-8")) + "\n"
        expNoteNum = 1
        while expNoteNum < 1000:
            if 'Experiment_Note_' + str(expNoteNum) in self.f['Miscellaneous'].keys():
                infoStr += "Extra Experiment Note #" + str(expNoteNum) + ": " + str(self.f['Miscellaneous']['Experiment_Note_' + str(expNoteNum)][0].decode("utf-8")) + "\n"
                expNoteNum += 1
            else: 
                break
        print(infoStr)
        return infoStr

    def get_experiment_time_and_date(self):
        start_date, stop_date, start_time, stop_time = '','','',''
        try:
            start_date = ''.join([x.decode('UTF-8') for x in self.f['Miscellaneous']['Start-Date']])
        except KeyError:
            pass
        try:
            start_time = ''.join([x.decode('UTF-8') for x in self.f['Miscellaneous']['Start-Time']])
        except KeyError:
            pass
        try:
            stop_date = ''.join([x.decode('UTF-8') for x in self.f['Miscellaneous']['Stop-Date']])
        except KeyError:
            pass
        try:
            stop_time = ''.join([x.decode('UTF-8') for x in self.f['Miscellaneous']['Stop-Time']])
        except KeyError:
            pass
        return start_date, start_time, stop_date, stop_time
        #return "","","",""

    def __allkeys(self, obj):
        "Recursively find all keys in an h5py.Group."
        keys = (obj.name,)
        if isinstance(obj, h5.Group):
            for key, value in obj.items():
                if isinstance(value, h5.Group):
                    keys = keys + self.__allkeys(value)
                else:
                    keys = keys + (value.name,)
        return keys

    def print_all_keys(self):
        """
        print keys name and keys value row by row
        """
        exp_all_keys = self.__allkeys(self.get_params())
        exp_key_name = [keys for keys in exp_all_keys if len(keys.split('/'))==4]
        _param = self.get_params()
        print('{:<25s}:{:>10s}'.format('Name','Value'))
        for idx, _key_name in enumerate(exp_key_name):
            print('{:<25s}:{:>10.2f}'.format(
                _param[_key_name+'/Name'][()].tobytes().decode("utf-8"),
                _param[_key_name+'/Constant Value'][0]))

if __name__ == "__main__":
    print("I am expfile")
if __name__=="ExpFile":
    print("I am imported expfile")
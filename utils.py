import configparser as ConfigParser
from optparse import OptionParser
import numpy as np
#import scipy.io.wavfile
import os
import soundfile as sf
import torch
from torch.autograd import Variable

def ReadList(list_file):
    f=open(list_file,"r",encoding='utf8')
    lines=f.readlines()
    list_sig=[]
    for x in lines:
            list_sig.append(x.rstrip())
    f.close()
    return list_sig

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError

def read_conf(cfg_file = None):

    parser=OptionParser()
    if cfg_file is None:
        parser.add_option("--cfg") # Mandatory
        (options,args)=parser.parse_args()
        cfg_file=options.cfg
    else:
        options = OptionParser().get_default_values()
    Config = ConfigParser.ConfigParser()
    Config.read(cfg_file)

    #[data]
    options.tr_lst=os.path.normpath(Config.get('data', 'tr_lst'))
    options.te_lst=os.path.normpath(Config.get('data', 'te_lst'))
    options.lab_dict=os.path.normpath(Config.get('data', 'lab_dict'))
    options.data_folder=os.path.normpath(Config.get('data', 'data_folder'))
    options.output_folder=os.path.normpath(Config.get('data', 'output_folder'))
    options.pt_file=os.path.normpath(Config.get('data', 'pt_file'))

    #[windowing]
    options.fs=Config.get('windowing', 'fs')
    options.cw_len=Config.get('windowing', 'cw_len')
    options.cw_shift=Config.get('windowing', 'cw_shift')

    #[cnn]
    options.cnn_N_filt=Config.get('cnn', 'cnn_N_filt')
    options.cnn_len_filt=Config.get('cnn', 'cnn_len_filt')
    options.cnn_max_pool_len=Config.get('cnn', 'cnn_max_pool_len')
    options.cnn_use_laynorm_inp=Config.get('cnn', 'cnn_use_laynorm_inp')
    options.cnn_use_batchnorm_inp=Config.get('cnn', 'cnn_use_batchnorm_inp')
    options.cnn_use_laynorm=Config.get('cnn', 'cnn_use_laynorm')
    options.cnn_use_batchnorm=Config.get('cnn', 'cnn_use_batchnorm')
    options.cnn_act=Config.get('cnn', 'cnn_act')
    options.cnn_drop=Config.get('cnn', 'cnn_drop')

    #[dnn]
    options.fc_lay=Config.get('dnn', 'fc_lay')
    options.fc_drop=Config.get('dnn', 'fc_drop')
    options.fc_use_laynorm_inp=Config.get('dnn', 'fc_use_laynorm_inp')
    options.fc_use_batchnorm_inp=Config.get('dnn', 'fc_use_batchnorm_inp')
    options.fc_use_batchnorm=Config.get('dnn', 'fc_use_batchnorm')
    options.fc_use_laynorm=Config.get('dnn', 'fc_use_laynorm')
    options.fc_act=Config.get('dnn', 'fc_act')

    #[class]
    options.class_lay=Config.get('class', 'class_lay')
    options.class_drop=Config.get('class', 'class_drop')
    options.class_use_laynorm_inp=Config.get('class', 'class_use_laynorm_inp')
    options.class_use_batchnorm_inp=Config.get('class', 'class_use_batchnorm_inp')
    options.class_use_batchnorm=Config.get('class', 'class_use_batchnorm')
    options.class_use_laynorm=Config.get('class', 'class_use_laynorm')
    options.class_act=Config.get('class', 'class_act')

    #[optimization]
    options.lr=Config.get('optimization', 'lr')
    options.batch_size=Config.get('optimization', 'batch_size')
    options.N_epochs=Config.get('optimization', 'N_epochs')
    options.N_batches=Config.get('optimization', 'N_batches')
    options.N_eval_epoch=Config.get('optimization', 'N_eval_epoch')
    options.seed=Config.get('optimization', 'seed')

    return options
	
def create_batches_rnd(batch_size, data_folder, wav_lst, N_snt, wlen, lab_dict, fact_amp):
    
    # Initialization of the minibatch (batch_size,[0=>x_t,1=>x_t+N,1=>random_samp])
    sig_batch = np.zeros([batch_size, wlen])
    lab_batch = np.zeros(batch_size)
  
    snt_id_arr = np.random.randint(N_snt, size=batch_size)
 
    rand_amp_arr = np.random.uniform(1.0-fact_amp, 1.0+fact_amp, batch_size)

    for i in range(batch_size):

        path = os.path.join(data_folder, wav_lst[snt_id_arr[i]])

        [signal, fs] = sf.read(path)

        # accesing to a random chunk
        snt_len = signal.shape[0]
        snt_beg = np.random.randint(snt_len-wlen-1) #randint(0, snt_len-2*wlen-1)
        snt_end = snt_beg+wlen

        channels = len(signal.shape)
        if channels == 2:
            print('WARNING: stereo to mono: '+ path)
            signal = signal[:,0]

        sig_batch[i,:]=signal[snt_beg:snt_end]*rand_amp_arr[i]
        lab_batch[i]=lab_dict[wav_lst[snt_id_arr[i]]]

    inp=Variable(torch.from_numpy(sig_batch).float().cuda().contiguous())
    lab=Variable(torch.from_numpy(lab_batch).float().cuda().contiguous())

    return inp,lab

def get_rnd_chunk(file_path, wlen):
    [signal, fs] = sf.read(os.path.normpath(file_path))
    # accesing to a random chunk
    snt_len = signal.shape[0]
    snt_beg = np.random.randint(snt_len-wlen-1) #randint(0, snt_len-2*wlen-1)
    snt_end = snt_beg+wlen

    if len(signal.shape) == 2:
        signal = signal[:,0]
    return signal[snt_beg:snt_end]
from flask import Flask, render_template
import os
import numpy as np
import fnmatch
import datetime
import warnings
import pyfits

warnings.filterwarnings("ignore", category=Warning)

app = Flask(__name__)
app.config['ROOT_DIR'] = r'/home/makov/tmp/tomo_root/Raw/2012_10_22/bone_Cu15x10_30x1sec/original'
#app.config['ROOT_DIR'] = r'/media/tmp/flash_backup/2cryst'
app.config['FILES_LIST'] = []
app.config['FILES_INFO'] = {}


@app.route('/')
def index():
    update_files_list(app.config['ROOT_DIR'], app.config['FILES_LIST'])
    update_files_info(app.config['FILES_LIST'], app.config['FILES_INFO'])
    file_list = sorted(app.config['FILES_INFO'].iteritems(), key=lambda (k, v): v['mtime'])
    sub_list = file_list[100:]
    for file_name, info in sub_list:
        if not 'intens' in info:
            info['intens'] = get_file_intensity(file_name)

    data = []
    current_group = None
    for file_name, info in sub_list:
        group_name = get_group_name(file_name)
        if current_group is None:
            current_group = group_name
            current_series = []
        elif not group_name == current_group:
            data.append({'label': current_group, 'data': current_series})
            current_group = group_name
            current_series = []
        current_series.append((info['mtime']*1000+14400000, info['intens']))
    else:
        data.append({'label': current_group, 'data': current_series})

    return render_template('index.html', data=data)


def update_files_list(root_dir, files_list):
    """
    get list of files and sort it by modification time
    """
    for root, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, '*.fit'):
            fname = os.path.join(root, filename)
            if not fname in files_list:
                files_list.append(fname)


def update_files_info(files_list, files_info):
    for f in files_list:
        if not f in files_info:
            stat = os.stat(f)
            mtime = stat.st_mtime
            t = {'mtime': mtime}
            files_info[f] = t


def get_frame_from_file(file_path):
    """
    Get array from fits file (FIAN dialect :) )

    :param file_path: Path to fits file
    :return: numpy array of float32
    :raise: IOError if input file not exists.
    """
    if os.path.exists(file_path):
        fi = pyfits.open(file_path, ignore_missing_end=True)
        a = np.array(fi[0].data, dtype='uint16').astype('float32')
        fi.close()
        return a
    else:
        raise IOError(str.format('File {0} not found.', file_path))


def get_file_intensity(file_path):
    data = get_frame_from_file(file_path)
    return data.sum()/(np.prod(data.shape))


def get_group_name(file_path):
    fname = os.path.split(file_path)[-1]
    group_name = fname.split('_')[0]
    return group_name


if __name__ == '__main__':
    app.run(debug=True)

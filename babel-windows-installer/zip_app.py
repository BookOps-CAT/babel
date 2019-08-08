import os
from zipfile import ZipFile


def collect_files(dist_directory):

    file_paths = []

    for root, directories, files in os.walk(dist_directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    comm_prefix = os.path.commonpath(file_paths)
    start = len(comm_prefix)

    arc_files = []
    for file in file_paths:
        arc_files.append((file, file[start + 1:]))

    return arc_files


def pack(dist_directory, zip_fh):

    files = collect_files(dist_directory)

    # write file to zipfile
    with ZipFile(zip_fh, 'w') as zip:
        for file, arcname in files:
            zip.write(file, arcname=arcname)

    print('All Babel files were zipped :-)')


if __name__ == "__main__":
    zip_name = 'babel2.zip'
    # dist_directory = './babel'
    dist_directory = r'C:\Users\tomaszkalata\scripts\Babel2\Archive\v2.0.0\dist\babel'
    pack(dist_directory, zip_name)

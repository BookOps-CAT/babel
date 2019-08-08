import os
from zipfile import ZipFile


def collect_files(dist_directory):

    file_paths = []

    for root, directories, files in os.walk(dist_directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    return file_paths


def pack(dist_directory, zip_fh):

    files = collect_files(dist_directory)

    print('Zipping following files:')
    for file in files:
        print(file)

    # write file to zipfile
    with ZipFile(zip_fh, 'w') as zip:
        for file in files:
            zip.write(file)

    print('All Babel files were zipped :-)')


if __name__ == "__main__":
    zip_name = 'babel2.zip'
    dist_directory = './babel'
    files = pack(dist_directory, zip_name)

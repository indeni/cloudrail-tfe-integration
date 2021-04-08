import os
import shutil
from natsort import natsorted


def split(source: str, dest_folder: str, write_size_bytes: int) -> int:
    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)
    os.mkdir(dest_folder)
    files_parts = 0
    with open(source, 'rb') as input_file:
        while True:
            chunk = input_file.read(write_size_bytes)
            # End the loop if we have hit EOF
            if not chunk:
                break
            files_parts += 1
            file_name = os.path.join(dest_folder, ('part_{}'.format(files_parts)))
            dest_file = open(file_name, 'wb')
            dest_file.write(chunk)
            dest_file.close()
    return files_parts


def join(source_dir: str, dest_file: str, read_size_bytes: int):
    parts = os.listdir(source_dir)
    sorted_parts = natsorted(parts)
    with open(dest_file, 'wb') as output_file:
        for file in sorted_parts:
            path = os.path.join(source_dir, file)
            with open(path, 'rb') as input_file:
                while True:
                    bytes_read = input_file.read(read_size_bytes)
                    # Break out of loop if we are at EOF
                    if not bytes_read:
                        break
                    output_file.write(bytes_read)

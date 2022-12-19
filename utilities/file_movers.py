import shutil
import os

from tqdm import tqdm

# from utilities.slides_to_moving_picture_show import make_moving_picture_show
from utilities.utilities import automkdir, datetime_string


def copy_logfiles_default_params(
        base_folder_to_move="D:/PythonProjects/ProjectArchangel-AbstractCases-2022-10-15/logfiles/",
        destination="D:/Users/seang/OneDrive - polymtl.ca/project-archangel-logfiles/"
):
    copy_logfiles(base_folder_to_move, destination)


def copy_logfiles(base_folder_to_move, destination):
    for src_dir, dirs, files in os.walk(base_folder_to_move):
        dst_dir = src_dir.replace(base_folder_to_move, destination, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in tqdm(files):
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                # in case of the src and dst are the same file
                if os.path.samefile(src_file, dst_file):
                    continue
                os.remove(dst_file)
            shutil.copy(src_file, dst_dir)


def move_results_files_utilities(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in tqdm(files):
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                # in case of the src and dst are the same file
                if os.path.samefile(src_file, dst_file):
                    continue
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)
    file_names = list(os.listdir(root_src_dir))
    for file_name in tqdm(file_names):
        shutil.rmtree(os.path.join(root_src_dir, file_name))


def default_parms_move_results_files_utilities(
        base_folders_to_move="D:/PythonProjects/ProjectArchangel-AbstractCases-2022-10-15/outputs/",
        destinations="G:/project-archangel/outputs/"
):
    if isinstance(base_folders_to_move, list) and isinstance(destinations, list):
        for folder, destination in zip(base_folders_to_move, destinations):
            move_results_files_utilities(folder, destination)
    elif isinstance(base_folders_to_move, str) and isinstance(destinations, str):
        move_results_files_utilities(base_folders_to_move, destinations)
    else:
        print(f"Bruh what the hell is wrong with you")
        raise Exception(f"Bruh what the hell is wrong with you")


if __name__ == '__main__':
    default_parms_move_results_files_utilities(
        base_folders_to_move=f"D:/PythonProjects/ProjectArchangel-AbstractCases-2022-10-15/outputs/",
        destinations=f"G:/OUTPUTS-project-archangel-AbstractCases/"
    )


def clean_up(
        open_the_folder=False,
        base_folders_to_move=f"D:/PythonProjects/ProjectArchangel-AbstractCases-2022-10-15/outputs/",
        destinations=f"G:/OUTPUTS-project-archangel-AbstractCases/",
        LOGFILE_base_folder_to_move="D:/PythonProjects/ProjectArchangel-AbstractCases-2022-10-15/logfiles/",
        LOGFILE_destination="D:/Users/seang/OneDrive - polymtl.ca/project-archangel-logfiles/"
):
    try:
        print(f"Moving folders...")
        default_parms_move_results_files_utilities(
            base_folders_to_move=base_folders_to_move,
            destinations=destinations
        )
        if open_the_folder:
            open_folder(f"G:/OUTPUTS-project-archangel-AbstractCases/{datetime_string()}")
    except:
        print(f"Failed to move folders... will try again later")
    try:
        print(f"Copying log files")
        copy_logfiles_default_params(
            base_folder_to_move=LOGFILE_base_folder_to_move,
            destination=LOGFILE_destination
        )
        if open_the_folder:
            open_folder("D:/Users/seang/OneDrive - polymtl.ca/project-archangel-logfiles/")
    except:
        print(f"Failed to copy log files... will try again later")


def open_folder(folder):
    try:
        os.startfile(os.path.realpath(F"{folder}/"))
    except:
        print(f"Could not find folder : {folder}")


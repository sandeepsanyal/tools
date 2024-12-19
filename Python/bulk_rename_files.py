import os

directory = r"/Volumes/2tb_m2/tv_series/The Office/Season 9"

for file in os.listdir(directory):
    old_file = directory + r"/" + file
    new_file = old_file.replace(r"The Office (US) (2005) - ", "").replace(r" (1080p BluRay x265 Silence)", "")

    os.rename(old_file, new_file)
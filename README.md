# MCMapCropper

Made this to automatically crop many exported Minecraft minimaps ([exported from Xaero's World Map mod](https://www.curseforge.com/minecraft/mc-mods/xaeros-world-map)) to the same location.

## How to Use

1. Add image files into `input` folder. <sub>All image files are in `.png` format.</sub>
   * Minimap images can be placed in the `/input/maps/` folder.
   * *Templates* can be placed in the `/input/templates/` folder.\
     Templates are used as a reference for where to crop the image.
     You can make a copy of any of your input images and crop the copy to the area that you want to crop all the other images to.
2. Install requirements
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
3. Select template file to use if prompted.
4. Output images should appear in `/output/`.

## Samples
Sample files can be found in this repo in `/input.example/` and `/output.example/`.

You can run the script on the example input files by renaming `/input.example/` to `/input/` and following the instructions above.
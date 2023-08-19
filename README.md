Whorestone Tracker is a Python script used to manage .dds files used for Hearthstone modding with SpecialK.

# Getting Started

## Windows

* Install Python 3 from [this website](https://www.python.org/downloads/windows/)

* Open Command Prompt

* Install Pip:

```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

* Install requirements and run the script:

```bash
py -m pip install -r requirements.txt
python wstone.py
```

## Mac/Linux

* Open Terminal

* Install Pip:

```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

* Install requirements and run the script:

```bash
pip install -r requirements.txt
python3 wstone.py
```

## Adding a Directory

Go to `File > Open Texture Directory...` and choose the `inject` directory in your `SK_Res` folder.

# Features

## File Display

Visually displays all .dds textures files in your `inject` directory of choice. Also saves the location of all current .dds files in a JSON file.

## Right-Click Context Menu

Right-click any file within the file display to show a context menu. From there, you can change the ID or hex code of an entry, or delete the file altogether.

## ID Association

Associates each texture file with an ID, usually card name, for searching and remapping.

## Search

Search .dds file with regex. Matches either hex code or ID.

## Duplicate Removal

Find duplicate .dds files in separate directories and pick one to keep.

> WARNING: Whorestone Tracker is still under development and is not full tested. Any files deleted by the duplicate remover cannot be recovered afterwards. Consider making a backup before using this feature.

## Remapping

Use a `.csv` file to rename a large group of .dds files programatically. The .csv file must have the format:

```csv
hex,id
[hex code 1],[id 1]
[hex code 2],[id 2]
[hex code 3],[id 3]
...
```

similar to `FullTextureList.csv`.

### How It Works

Let's say we have our current `FullTextureList.csv`:

```csv
hex,id
00000001,Circle of Healing
00000002,Holy Smite
```

And a new mapping `.csv` file:

```csv
hex,id
00000003,Circle of Healing
00000004,Prophet Velen
```

We first replace old existing mappings with new ones in `FullTextureList.csv`:

```csv
hex,id
00000003,Circle of Healing
00000002,Holy Smite
```

We then concatenate both `.csv` files:

```csv
hex,id
00000003,Circle of Healing
00000002,Holy Smite
00000003,Circle of Healing
00000004,Prophet Velen
```

And finally remove any duplicates.

```csv
hex,id
00000003,Circle of Healing
00000002,Holy Smite
00000004,Prophet Velen
```

# How to Contribute

## Add to `FullTextureList.csv`

`FullTextureList.csv` is not complete and needs more mappings from hex codes to IDs. Help to write descriptive IDs for each texture hash.

## Bug Reporting

Report any bugs encountered when using the app.

## Feature Requests/Implementations

Any new features which improve the tracker are welcome.

import os
import glob
import json
import pandas as pd
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, IntVar, StringVar, Menu, messagebox

class MainWindow:

    #   data is a dict which contains:
    #       tex_dir - the main texture directory
    #       options - miscellaneous options
    #   texdirname is a StringVar which copies data['tex_dir']
    #   texidname is a StringVar, the id of the current texture from mapping_df
    #   mapping_df is a dataframe derived from FullTextureList.csv
    #   tex_df is a dataframe which contains:
    #       tex_relpath - relative path of .dds file
    #       tex_hex - isolated hex code of .dds file
    #       tex_id - name of the texture derived from mapping_df
    #   search_query is used to search IDs and hex codes
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry('800x600')
        self.root.resizable(False, False)
        self.root.title('Whorestone Tracker')

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.texdirname = StringVar()
        self.texdirname.set('No path selected')

        self.texidname = StringVar()
        self.texidname.set('No image selected')

        self.search_query = StringVar()
        self.search_query.set('')

        self.load()
        self.draw()

    def save(self):
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
    
    def load(self):
        if os.path.isfile('data.json'):
            try:
                f = open('data.json')
                self.data = json.loads(f.read())
            except ValueError:
                self.data = {}
        else:
            self.data = {}
        
        if os.path.isfile('FullTextureList.csv'):
            try:
                self.mapping_df = pd.read_csv('FullTextureList.csv')
            except ValueError:
                self.mapping_df = pd.DataFrame()
        else:
            self.mapping_df = pd.DataFrame()
        
        if 'tex_dir' in self.data:
            self.load_folderpath(self.data['tex_dir'])
        else:
            self.data['tex_dir'] = ''
            self.tex_df = pd.DataFrame()
    
        if 'options' not in self.data:
            self.data['options'] = {}
            self.data['options']['flip_image'] = True
    
    def load_folderpath(self, folderpath):
        self.texdirname.set('Path: ' + folderpath)
        self.data['tex_dir'] = folderpath
        fullimgpath = glob.glob(folderpath + '/**/*.dds', recursive=True)
        tex_relpath = [os.path.relpath(fip, folderpath) for fip in fullimgpath]
        tex_hex = [os.path.basename(rp).split('.')[0] for rp in tex_relpath]
        tex_id = []

        for hx in tex_hex:
            try:
                tex_id.append(self.mapping_df.loc[self.mapping_df['hex'] == hx]['id'].values[0])
            except (KeyError, IndexError) as e:
                tex_id.append(None)
        
        tex_dict = {"tex_relpath": tex_relpath, "tex_hex": tex_hex, 'tex_id': tex_id}
        self.tex_df = pd.DataFrame(tex_dict)
        self.tex_search_df = self.tex_df

    def reload(self):
        self.load_folderpath(self.data['tex_dir'])
        self.tex_search_df = self.tex_df
        self.searchbox.delete(0, tk.END)
        self.tex_search_df.reset_index(inplace = True, drop = True)
        self.listbox.delete(0, tk.END)
        for img in self.tex_search_df['tex_hex']:
            self.listbox.insert(tk.END, img)

    def draw(self):
        left_frame = tk.Frame(self.root, width=350, height=600)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        right_frame = tk.Frame(self.root, width=450, height=600)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        menubar = Menu(self.root)
    
        fileMenu = Menu(menubar, tearoff=0)
        fileMenu.add_command(label="Open Texture Directory...", command=self.open_folder)
        fileMenu.add_command(label="Reload Directory", command=self.reload)
        menubar.add_cascade(label="File", menu=fileMenu)

        toolsMenu = Menu(menubar, tearoff=0)
        toolsMenu.add_command(label="Find Duplicates", command=self.find_duplicates)
        toolsMenu.add_command(label="Remap...", command=self.remap)
        menubar.add_cascade(label="Tools", menu=toolsMenu)
    
        optionsMenu = Menu(menubar, tearoff=0)
        optionsMenu.add_command(label="Flip Image", command=self.set_flip_image)
        menubar.add_cascade(label="Options", menu=optionsMenu)
    
        self.root.config(menu=menubar)
    
        try:
            im = Image.open(os.path.join(self.data['tex_dir'], self.tex_df['tex_relpath'][0]))
            im = im.resize((500, 500), Image.LANCZOS)
            if self.data['options']['flip_image']:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            self.photo_image = ImageTk.PhotoImage(im)
        except KeyError:
            im = Image.new('RGB', (500, 500))
            self.photo_image = ImageTk.PhotoImage(im)
        
        self.searchbox = tk.Entry(
            left_frame, 
            width=30,
            textvariable=self.search_query
        )

        self.searchbox.bind('<KeyRelease>', self.on_update_search)
        self.searchbox.pack(side=tk.TOP)
    
        self.listbox = tk.Listbox(
            left_frame, 
            bg = "white",
            activestyle = 'dotbox',
            yscrollcommand = tk.Scrollbar.set
        )
    
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        listscrollbar = tk.Scrollbar(self.listbox)
        listscrollbar.pack(side = tk.RIGHT, fill = tk.BOTH)
        self.listbox.config(yscrollcommand = listscrollbar.set)
        listscrollbar.config(command = self.listbox.yview)

        try:
            for img in self.tex_df['tex_hex']:
                self.listbox.insert(tk.END, img)
        except KeyError:
            pass
    
        self.listbox.pack(fill="both", expand=True)
    
        dirlabel = tk.Label(
            right_frame,
            textvariable=self.texdirname,
            wraplength=700,
            justify=tk.LEFT,
            width=60,
            height=2
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )
    
        self.canvas = tk.Canvas(
            right_frame,
            width=500,
            height=500
        )
        self.canvas.grid(
            row=1,
            column=0, 
            padx=5, 
            pady=5
        )
        self.image_output = self.canvas.create_image(
            0, 
            0,
            image=self.photo_image,
            anchor = tk.NW
        )

        idlabel = tk.Label(
            right_frame,
            textvariable=self.texidname,
            wraplength=700,
            justify=tk.LEFT,
            width=60,
            height=2
        ).grid(
            row=2,
            column=0,
            padx=5,
            pady=5
        )
    
        self.root.mainloop()

    def open_folder(self):
        folderpath = filedialog.askdirectory()

        if not os.path.exists(folderpath):
            return
        
        self.load_folderpath(folderpath)
        self.save()
        self.listbox.delete(0, tk.END)
        for img in self.tex_df['tex_hex']:
            self.listbox.insert(tk.END, img)

    def on_select(self, evt):
        # evt is an event object
        curselection = evt.widget.curselection()
        if curselection == ():
            return
        
        index = int(curselection[0])
        im = Image.open(os.path.join(self.data['tex_dir'], self.tex_search_df['tex_relpath'][index] ))

        if self.tex_search_df['tex_id'][index] is not None:
            self.texidname.set('ID: ' + self.tex_search_df['tex_id'][index])
        else:
            self.texidname.set('No ID set')
        
        im = im.resize((500, 500), Image.LANCZOS)
        if self.data['options']['flip_image']:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        self.photo_image = ImageTk.PhotoImage(im)
        self.canvas.itemconfigure(self.image_output, image=self.photo_image)

    def on_update_search(self, evt):
        sq = self.search_query.get()
        print(sq)
        if sq:
            df1 = self.tex_df[self.tex_df['tex_id'].str.contains(sq, na=False)]
            df2 = self.tex_df[self.tex_df['tex_hex'].str.contains(sq, na=False)]
            self.tex_search_df = pd.concat([df1, df2], ignore_index=True, sort=False).drop_duplicates(keep='first')
            self.tex_search_df.reset_index(inplace = True, drop = True)
            print(self.tex_search_df.head)
            self.listbox.delete(0, tk.END)
            for img in self.tex_search_df['tex_hex']:
                self.listbox.insert(tk.END, img)
        else:
            self.listbox.delete(0, tk.END)
            self.tex_search_df = self.tex_df
            for img in self.tex_df['tex_hex']:
                self.listbox.insert(tk.END, img)

    def set_flip_image(self):
        self.data['options']['flip_image'] = not self.data['options']['flip_image']

    def find_duplicates(self):
        dupewindow = DupeWindow(self.root, self.data, self.tex_df)
        self.reload()
    
    def remap(self):
        print("Remap!")

class DupeWindow:
    def __init__(self, root, data, tex_df):
        self.dupe_window = tk.Toplevel(root)
        self.dupe_window.resizable(False, False)
        self.dupe_window.title('Duplicate Finder')
        self.dupe_window.grab_set()

        self.dupe_window.grid_rowconfigure(0, weight=1)
        self.dupe_window.grid_columnconfigure(2, weight=1)

        self.draw()
        self.modified_tex_df = pd.DataFrame()

        name_dict = {}
        for i in tex_df['tex_relpath']:
            hex = tex_df.loc[tex_df['tex_relpath'] == i]['tex_hex'].values[0]
            if hex not in name_dict:
                name_dict[hex] = i
            else:
                self.dupe_text_1.set(name_dict[hex])
                self.dupe_text_2.set(i)

                im1 = Image.open(os.path.join(data['tex_dir'], name_dict[hex]))
                im1 = im1.resize((500, 500), Image.LANCZOS)
                if data['options']['flip_image']:
                    im1 = im1.transpose(Image.FLIP_TOP_BOTTOM)
                photo_image_1 = ImageTk.PhotoImage(im1)
                self.comp_canvas_1.itemconfigure(self.dupe_output_1, image=photo_image_1)

                im2 = Image.open(os.path.join(data['tex_dir'], i))
                im2 = im2.resize((500, 500), Image.LANCZOS)
                if data['options']['flip_image']:
                    im2 = im2.transpose(Image.FLIP_TOP_BOTTOM)
                photo_image_2 = ImageTk.PhotoImage(im2)
                self.comp_canvas_2.itemconfigure(self.dupe_output_2, image=photo_image_2)

                self.dupe_window.wait_variable(self.dupe_wait_var)

                if self.dupe_wait_var.get() == 1:
                    # Delete 2
                    os.remove(os.path.join(data['tex_dir'], i))
                    tex_df = tex_df[tex_df.tex_relpath != i]
                elif self.dupe_wait_var.get() == 2:
                    # Delete 1
                    os.remove(os.path.join(data['tex_dir'], name_dict[hex]))
                    tex_df = tex_df[tex_df.tex_relpath != name_dict[hex]]
                    name_dict[hex] = i
        
        messagebox.showinfo("Information", "Operation successful.")
        self.dupe_window.destroy()
    
    def draw(self):
        dupe_left_frame = tk.Frame(self.dupe_window, width=640, height=600)
        dupe_left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        dupe_right_frame = tk.Frame(self.dupe_window, width=640, height=600)
        dupe_right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        im = Image.new('RGB', (500, 500))
        dupe_image_1 = ImageTk.PhotoImage(im)
        dupe_image_2 = ImageTk.PhotoImage(im)

        self.comp_canvas_1 = tk.Canvas(
            dupe_left_frame,
            width=500,
            height=500
        )
        self.comp_canvas_1.grid(
            row=0,
            column=0, 
            padx=5, 
            pady=5
        )
        self.dupe_output_1 = self.comp_canvas_1.create_image(
            0, 
            0,
            image=dupe_image_1,
            anchor = tk.NW
        )

        self.comp_canvas_2 = tk.Canvas(
            dupe_right_frame,
            width=500,
            height=500
        )
        self.comp_canvas_2.grid(
            row=0,
            column=0, 
            padx=5, 
            pady=5
        )
        self.dupe_output_2 = self.comp_canvas_2.create_image(
            0, 
            0,
            image=dupe_image_2,
            anchor = tk.NW
        )

        self.dupe_text_1 = tk.StringVar()
        self.dupe_text_1.set('test1')
        self.dupe_text_2 = tk.StringVar()
        self.dupe_text_2.set('test2')

        dupe_label_1 = tk.Label(
            dupe_left_frame,
            textvariable=self.dupe_text_1,
            width=60,
            height=2
        ).grid(
            row=1,
            column=0,
            padx=5,
            pady=5
        )

        dupe_label_2 = tk.Label(
            dupe_right_frame,
            textvariable=self.dupe_text_2,
            width=60,
            height=2,
        ).grid(
            row=1,
            column=0,
            padx=5,
            pady=5
        )

        self.dupe_wait_var = tk.IntVar()

        dupe_button_1 = tk.Button(
            dupe_left_frame,
            text='Select 1',
            width=40,
            height=2,
            command=lambda : self.dupe_wait_var.set(1)
        ).grid(
            row=2,
            column=0,
            padx=5,
            pady=5
        )

        dupe_button_2 = tk.Button(
            dupe_right_frame,
            text='Select 2',
            width=40,
            height=2,
            command=lambda : self.dupe_wait_var.set(2)
        ).grid(
            row=2,
            column=0,
            padx=5,
            pady=5
        )

        dupe_button_2 = tk.Button(
            self.dupe_window,
            text='Skip',
            width=40,
            height=2,
            command=lambda : self.dupe_wait_var.set(0)
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            padx=5,
            pady=5
        )

main = MainWindow()

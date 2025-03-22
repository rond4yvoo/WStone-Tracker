import os
import sys
import glob
import json
import re
import pandas as pd
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, IntVar, StringVar, Menu, messagebox

class MainWindow:

    #   data is a dict which contains:
    #       tex_dir - the main texture directory
    #       options - miscellaneous options
    #   data_path is the path to data.json
    #   texdirname is a StringVar which copies data['tex_dir']
    #   texidname is a StringVar, the id of the current texture from mapping_df
    #   mapping_df is a dataframe derived from final.csv
    #   mapping_df_path is the path to final.csv
    #   tex_df is a dataframe which contains:
    #       tex_relpath - relative path of .dds file
    #       tex_hex - isolated hex code of .dds file
    #       tex_id - name of the texture derived from mapping_df
    #   search_query is used to search IDs and hex codes
    
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
        elif __file__:
            self.application_path = os.path.dirname(__file__)

        self.root = tk.Tk()
        self.root.geometry('800x650')
        self.root.resizable(False, False)
        self.root.title('Whorestone Tracker')

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.mapping_df_path = os.path.join(self.application_path, 'csv', 'final.csv')
        self.data_path = os.path.join(self.application_path, 'data.json')

        self.texdirname = StringVar()
        self.texdirname.set('No path selected')

        self.texidname = StringVar()
        self.texidname.set('No image selected')

        self.search_query = StringVar()
        self.search_query.set('')

        self.load()
        self.draw()

    def save(self):
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
    
    def load(self):
        if os.path.isfile(self.data_path):
            try:
                f = open(self.data_path)
                self.data = json.loads(f.read())
            except ValueError:
                self.data = {}
        else:
            self.data = {}
        
        if os.path.isfile(self.mapping_df_path):
            try:
                self.mapping_df = pd.read_csv(self.mapping_df_path)
            except ValueError:
                messagebox.showwarning('Warning', 'final.csv cannot be found, or does not have the right format.')
                pd.DataFrame(columns=['hex', 'id'])
        else:
            messagebox.showwarning('Warning', 'final.csv cannot be found, or does not have the right format.')
            pd.DataFrame(columns=['hex', 'id'])
        
        if 'tex_dir' in self.data:
            self.load_folderpath(self.data['tex_dir'])
        else:
            self.data['tex_dir'] = ''
            self.tex_df = pd.DataFrame(columns=['tex_relpath', 'tex_hex', 'tex_id'])
    
        if 'options' not in self.data:
            self.data['options'] = {}
            self.data['options']['flip_image'] = True
    
    def load_folderpath(self, folderpath):
        self.root.withdraw()
        loading_splash = LoadingSplash(self.root)

        self.texdirname.set('Path: ' + folderpath)
        self.data['tex_dir'] = folderpath
        fullimgpath = glob.glob(folderpath + '/**/*.[Dd][Dd][Ss]', recursive=True)
        tex_relpath = [os.path.relpath(fip, folderpath) for fip in fullimgpath]
        tex_hex = [os.path.basename(rp).split('.')[0] for rp in tex_relpath]
        tex_id = []

        for hx in tex_hex:
            try:
                tex_id.append(self.mapping_df.loc[self.mapping_df['texhash'] == hx]['cardname'].values[0])
            except (KeyError, IndexError) as e:
                tex_id.append(None)
        
        tex_dict = {'tex_relpath': tex_relpath, 'tex_hex': tex_hex, 'tex_id': tex_id}
        self.tex_df = pd.DataFrame(tex_dict)
        self.tex_search_df = self.tex_df

        loading_splash.destroy()
        self.root.deiconify()

    def reload(self):
        self.load_folderpath(self.data['tex_dir'])
        self.on_update_search(None)

    def draw(self):
        left_frame = tk.Frame(self.root, width=350, height=600)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        right_frame = tk.Frame(self.root, width=450, height=600)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        
        menubar = Menu(self.root)
    
        fileMenu = Menu(menubar, tearoff=0)
        fileMenu.add_command(label='Open Texture Directory...', command=self.open_folder)
        fileMenu.add_command(label='Reload Directory', command=self.reload)
        menubar.add_cascade(label='File', menu=fileMenu)

        toolsMenu = Menu(menubar, tearoff=0)
        toolsMenu.add_command(label='Find Duplicates', command=self.find_duplicates)
        toolsMenu.add_command(label='Remap...', command=self.remap)
        menubar.add_cascade(label='Tools', menu=toolsMenu)
    
        optionsMenu = Menu(menubar, tearoff=0)
        optionsMenu.add_command(label='Flip Image', command=self.set_flip_image)
        menubar.add_cascade(label='Options', menu=optionsMenu)
    
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
            bg = 'white',
            activestyle = 'dotbox',
            yscrollcommand = tk.Scrollbar.set
        )
    
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        listscrollbar = tk.Scrollbar(self.listbox)
        listscrollbar.pack(side = tk.RIGHT, fill = tk.BOTH)
        self.listbox.config(yscrollcommand = listscrollbar.set)
        listscrollbar.config(command = self.listbox.yview)

        aqua = self.root.tk.call('tk', 'windowingsystem') == 'aqua'
        # self.listbox.bind('<2>' if aqua else '<3>', self.on_right_click)

        try:
            for img in self.tex_df['tex_hex']:
                self.listbox.insert(tk.END, img)
        except KeyError:
            pass
    
        self.listbox.pack(fill='both', expand=True)
    
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

        if not folderpath or not os.path.exists(folderpath):
            return
        
        self.load_folderpath(folderpath)
        self.save()
        self.listbox.delete(0, tk.END)
        for img in self.tex_df['tex_hex']:
            self.listbox.insert(tk.END, img)

    def listbox_focus(self, index):
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

    def on_select(self, evt):
        # evt is an event object
        curselection = evt.widget.curselection()
        if curselection == ():
            return
        
        index = int(curselection[0])
        self.listbox_focus(index)

    def on_update_search(self, evt):
        sq = self.search_query.get()
        if sq:
            try:
                df1 = self.tex_df[self.tex_df['tex_id'].str.match(sq, na=False)]
                df2 = self.tex_df[self.tex_df['tex_hex'].str.match(sq, na=False)]
            except re.error: 
                return
            
            self.tex_search_df = pd.concat([df1, df2], ignore_index=True, sort=False).drop_duplicates(keep='first')
            self.tex_search_df.reset_index(inplace = True, drop = True)
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
        messagebox.showinfo('Information', 'Select mapping .csv file.')
        remap_file = filedialog.askopenfilename(filetypes =[('CSV files', '*.csv')])
        new_mapping_df = pd.DataFrame()

        if not remap_file or not os.path.exists(remap_file):
            messagebox.showerror('Error', 'Invalid .csv file.')
            return
        
        try:
            new_mapping_df = pd.read_csv(remap_file)
            self.mapping_df.rename(columns={"texhash": "old_texhash"})
        except (pd.errors.EmptyDataError, pd.errors.ParserError, KeyError) as e:
            messagebox.showerror('Error', 'Invalid .csv file.')
            return
        
        try:
            merged_df = new_mapping_df.merge(self.mapping_df, how='left', on=['guid', 'cardname', 'texname'])
            new_mapping_dict = pd.Series(merged_df['texhash'].values,index=merged_df['old_texhash']).to_dict()
            self.tex_df['tex_hex'] = self.tex_df['tex_id'].map(new_mapping_dict).fillna(self.tex_df['tex_hex'])

            for index, row in self.tex_df.iterrows():
                new_relpath = os.path.join(os.path.dirname(row['tex_relpath']), row['tex_hex'] + '.dds')
                os.rename(os.path.join(self.data['tex_dir'], row['tex_relpath']), os.path.join(self.data['tex_dir'], new_relpath))
        except KeyError:
            pass

        new_mapping_df.to_csv(self.mapping_df_path, index=False)
        self.reload()

    def on_right_click(self, evt):
        widget = evt.widget
        self.right_click_index = widget.nearest(evt.y)
        self.listbox.selection_clear(0,tk.END)
        self.listbox.selection_set(self.right_click_index)
        self.listbox.activate(self.right_click_index)
        self.listbox_focus(self.right_click_index)

        _, yoffset, _, height = widget.bbox(self.right_click_index)
        if evt.y > height + yoffset + 5: # XXX 5 is a niceness factor :)
            # Outside of widget.
            return

        menu = tk.Menu(tearoff=0)
        menu.tk_popup(evt.x_root, evt.y_root, 0)
        menu.grab_release()

        self.right_click_waitvar = tk.IntVar()
        self.right_click_stringvar = tk.StringVar()

    def right_click_draw(self, label_text, e_initial):
        self.input_window = tk.Toplevel(self.root)
        self.input_window.resizable(False, False)
        self.input_window.title('Input')
        self.input_window.grab_set()

        l = tk.Label(self.input_window, text=label_text)
        l.grid(column=0, row=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        e = tk.Entry(self.input_window, textvariable=self.right_click_stringvar)
        if e_initial:
            e.insert(0, e_initial)
        e.grid(column=0, row=1, columnspan=2, sticky="nsew", padx=5, pady=5)

        confirm_button = tk.Button(self.input_window, text='Confirm', command=lambda : self.right_click_waitvar.set(0))
        confirm_button.grid(column=0, row=2, padx=5, pady=5)

        cancel_button = tk.Button(self.input_window, text='Cancel', command=lambda : self.right_click_waitvar.set(1))
        cancel_button.grid(column=1, row=2, padx=5, pady=5)

        self.input_window.wait_variable(self.right_click_waitvar)
        self.input_window.destroy()

        if self.right_click_waitvar.get() == 0:
            return self.right_click_stringvar.get()
        else:
            return None
            
    def right_click_change_hex(self):
        curr_relpath = self.tex_search_df['tex_relpath'][self.right_click_index]
        curr_hex = self.tex_search_df['tex_hex'][self.right_click_index]
        curr_id = self.tex_search_df['tex_id'][self.right_click_index]
        
        output = self.right_click_draw('Enter new hex code.', curr_hex)

        if output:
            full_path = os.path.join(self.data['tex_dir'], self.tex_search_df['tex_relpath'][self.right_click_index])
            os.rename(full_path, os.path.join(self.data['tex_dir'], os.path.dirname(curr_relpath), output + '.dds'))

            try:
                search_index = self.mapping_df.loc[(self.mapping_df['hex'] == curr_hex) & (self.mapping_df['id'] == curr_id)].index[0]
                self.mapping_df['hex'][search_index] = output
            except IndexError:
                pass
            
            self.mapping_df.to_csv(self.mapping_df_path, index=False)
            self.reload()
    
    def right_click_delete_entry(self):
        response = tk.messagebox.askyesno(title='confirmation', message='Are you sure you want to delete this file?')

        if not response:
            return
        
        full_path = os.path.join(self.data['tex_dir'], self.tex_search_df['tex_relpath'][self.right_click_index])
        os.remove(full_path)
        self.reload()

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
        
        messagebox.showinfo('Information', 'Operation successful.')
        self.dupe_window.destroy()
    
    def draw(self):
        dupe_left_frame = tk.Frame(self.dupe_window, width=640, height=600)
        dupe_left_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        dupe_right_frame = tk.Frame(self.dupe_window, width=640, height=600)
        dupe_right_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

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

class LoadingSplash(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title("Loading")
        self.geometry('300x200')
        self.resizable(False, False)
        label = tk.Label(self, 
                 text="Loading...",
                 font=("Arial", 16, "bold"),      
                )
        
        label.grid(row=0, column=0)
        label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.update()

def main():
    main = MainWindow()

if __name__ == "__main__":
    main()

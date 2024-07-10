import tkinter
import tkinter.ttk
import tkinter.messagebox
import os
import re
import string
import ctypes
import sys
import configparser

from editable_treeview import EditableTreeview
from tkinterdnd2 import DND_FILES, TkinterDnD
from C2Py import C2PyHandler
from C2Py.C2PyEngine import *
from tkinter import filedialog

INDENT_TREE = '  '
properties = configparser.ConfigParser()  ## 클래스 객체 생성
properties.read('config.ini')  ## 파일 읽기

cfg_project_path = properties.get('DEFAULT','project_path')
cfg_include_path = list(map(lambda x : x.strip(), properties.get('DEFAULT','include_path').split(',')))
cfg_info_file_path = properties.get('DEFAULT','info_file_path')

parameter_description = {
'operations[0].' :'[0] Host operations',
'operations[1].' :'[1] RMW operations [rd]',
'operations[2].' :'[2] FUA operations [wr, SLC, OZ]',
'operations[3].' :'[3] Deallocate control data operations',
'operations[4].' :'[4] LOG operations [SLC, conds]',
'operations[5].' :'[5] PRM operations [rd]',
'operations[6].' :'[6] MTM operations [SLC]',
'operations[7].' :'[7] XOR block operations [SLC]',
'operations[8].' :'[8] XOR zone rebuild [rd, SLC, OZ]',
'operations[9].' :'[9] Active RS [rd]',
'operations[10].':'[10] FLGP [NOT SUPPORTED]',
'operations[11].' :'[11] Scan FWD [NOT SUPPORTED]',
'operations[12].' :'[12] Read headers [rd]',
'operations[13].' :'[13] RLC host VC [rd]',
'operations[14].' :'[14] RLC host blocks',
'operations[15].' :'[15] RLC MTM block [slc]',
'operations[16].' :'[16] RLC XOR blocks [slc]',
'operations[17].' :'[17] BRLC host blocks',
'operations[18].' :'[18] BRLC RLC blocks',
'operations[19].' :'[19] BRLC MTM blocks [slc]',
'operations[20].' :'[20] BRLC XOR blocks [slc]',
'operations[21].' :'[21] IFS blocks [slc]',
'operations[22].' :'[22] FADI blocks [slc]',
'operations[23].' :'[23] Boot blocks [slc]',
'operations[24].' :'[24] IFS directory blocks [slc, wr]',
'operations[25].' :'[25] Hostless operations [rd]',
'operationalStateChances' : '0:OPST 1:Mount 2:Power State 4:Normal',
'operationalStateChances' : '0:OPST 1:Mount 2:Power State 4:Normal',
'opTypeFailureChances' : '0:Read 1:Program 2:Erase 3:XOR recovery 4:DST 5:Data Retention Dection',
}

def remove_last_bracket(txt):
    r_txt = txt[::-1]    # creates reverse copy of txting
    if len(txt) == 0:
        return txt
    if r_txt[1] != ']':
        return txt

    for idx,c in enumerate(r_txt):
        if c == '[':
            break
    r_txt = txt[-1]+r_txt[idx+1:]
    txt = r_txt[::-1]
    return txt

def recursive_tree(obj_to_parse, tree_view, header="", obj_type=None, idx="",count=0,iid='', par_obj_type=None):
    """
    Print all values from the struct or union
    :param obj_type: The ctypes type of current object
    :param obj_to_parse: Prints values from given object
    :param header: Parents of current object
    :return: String representation of object
    """
    if issubclass(type(obj_to_parse), (ctypes.Structure, ctypes.Union)):
        # Go into every field in the struct and print it
        complete_result = "\n" if len(header.split(HIERARCHY_SEPARATOR)) > 1 else ""

        for idx,field in enumerate(obj_to_parse._fields_):
            field_name = field[0]
            field_type = field[1]
            curr_item = getattr(obj_to_parse, field_name)
            # Concatenate the items
            complete_result = (INDENT_TREE * len(header.split(HIERARCHY_SEPARATOR))) + header + field_name + \
                               ("" if issubclass(type(curr_item),
                                (ctypes.Structure, ctypes.Union)) else "[{}]".format(len(curr_item)) if issubclass(type(curr_item), (ctypes.Array)) else "")

            if par_obj_type is (ctypes.Array): # add array[] group field
                tree_view.insert(remove_last_bracket(header),'end',iid=header,text=INDENT_TREE * len(header.split(HIERARCHY_SEPARATOR))+header)
                par_obj_type = None # only one time. It is for array[0] , array[1], ... group
                
                # description setting
                if header in parameter_description:
                    tree_view.set(header, 'Desc',parameter_description[header])                    

            tree_view.insert(header,'end',iid=header + field_name + '.',text=complete_result) # add specific parameter name
            complete_result = recursive_tree(curr_item, tree_view, header + field_name + HIERARCHY_SEPARATOR, field_type,count=count+1) + \
                               ("" + ("" * (len(header.split(HIERARCHY_SEPARATOR)) - 1)) + "" if
                                len(header.split(HIERARCHY_SEPARATOR)) > 1 and obj_to_parse._fields_[-1] == field
                                else "")

            if len(tree_view.get_children(header + field_name + '.')) == 0: # if tree node have child, it is tree name. 
                tree_view.set(header + field_name + '.', 'Values',complete_result)
                print(header,field_name,complete_result)
                # description setting
                if field_name in parameter_description:
                    tree_view.set(header + field_name + '.', 'Desc',parameter_description[field_name])                      
        # Finally return the total string of the scope
        return complete_result
    elif issubclass(type(obj_to_parse), ctypes.Array):
        # Print every item in the array
        # The _array_ attribute is the original type of this array
        return '[' + ', '.join(recursive_tree(item, tree_view, header[:-1] + '[{}].'.format(idx), obj_to_parse._type_,idx,count=count+1,par_obj_type=ctypes.Array) for idx, item in enumerate(obj_to_parse)) + ']'
    elif obj_type in (ctypes.c_byte, ctypes.c_ubyte):
        # Print byte as a character if it is readable
        #return chr(obj_to_parse) if is_readable_char(obj_to_parse) else hex(obj_to_parse)
        return hex(obj_to_parse) # @todo WA: I don't need to print readable char.
    elif issubclass(type(obj_to_parse), (int, long)):
        # Print integers in hex
        return hex(obj_to_parse)
    else:
        return str(obj_to_parse)

class GUI():
    def __init__(self, master):      
        self.result_struct = None
        
        # tree view widget
        self.label_frame = tkinter.LabelFrame(master, text="Result")
        self.label_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        self.view = EditableTreeview(self.label_frame,columns=('Name','Value'),bind_key='<Double-Button-1>',data=[],non_editable_columns="#0",update_ei_struct_value=self.update_ei_struct_value)
        self.view.pack(side='left',fill='both',expand='y')       
        scrollbar = tkinter.ttk.Scrollbar(self.label_frame, orient=tkinter.VERTICAL, command=self.view.yview)
        self.view.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='left',fill='y')
    
        self.view.drop_target_register(DND_FILES)
        self.view.dnd_bind('<<Drop>>', lambda e: self.parse_binary(e.data))                
    
        self.view.heading('#0', text='Name')
        
        self.view['columns'] = ('Values','Desc')
        self.view.heading('Values', text='Values')                
        self.view.heading('Desc', text='Desc')                
        # end tree view widget    
        
        # text view widget
        self.label_frame_txt = tkinter.Frame(master)
        self.label_frame_txt.drop_target_register(DND_FILES)
        self.label_frame_txt.dnd_bind('<<Drop>>', lambda e: self.parse_binary(e.data))  
        self.label_frame_txt.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        label = tkinter.Label(self.label_frame_txt,text="Usage : Please drag EI bin file\nPrecondition : build Model (using Specific ei_config.i path)\n\nIf you want to change default path, please check 'config.ini'\nIf you complete model build, you can use your ei_config.i\n  path: repo\\_out\\Model\\DLLBuild\\atlas3_ei.RAM\\Instrumented\\Source\\FTL\\EI\\src\\ei_config.i\n", anchor="w",justify="left")
        label.pack(side='top',fill='x',expand=False)
        
        # @24.04.03 gcc build no support
        #input_box_frame = tkinter.LabelFrame(self.label_frame_txt,text='Project Path')
        #input_box_frame.pack(side='top',fill='x',expand=False)  
        #self.project_path = tkinter.StringVar()
        #proj_path_edit = tkinter.Entry(input_box_frame, textvariable=self.project_path)
        #proj_path_edit.pack(side='left',fill='x',expand=True)
        #self.project_path.set(os.path.abspath(cfg_project_path))
        
        input_box_frame = tkinter.LabelFrame(self.label_frame_txt,text='Bin Path')
        input_box_frame.pack(side='top',fill='x',expand=False)  
        self.bin_path = tkinter.StringVar()
        proj_path_edit = tkinter.Entry(input_box_frame, textvariable=self.bin_path)
        proj_path_edit.pack(side='left',fill='x',expand=True)
        self.select_bin_path = tkinter.Button(input_box_frame, text="...", command=lambda : self.select_path(self.bin_path.set,filetype=("bin files", "*.bin")))
        self.select_bin_path.pack(side='right',expand=False)  
        
        input_box_frame = tkinter.LabelFrame(self.label_frame_txt,text='Specific ei_config.i path')
        input_box_frame.pack(side='top',fill='x',expand=False)  
        self.ei_config_i_path = tkinter.StringVar()
        proj_path_edit = tkinter.Entry(input_box_frame, textvariable=self.ei_config_i_path)
        proj_path_edit.pack(side='left',fill='x',expand=True)
        self.ei_config_i_path.set(os.path.abspath(cfg_info_file_path))        
        self.select_config_i_path = tkinter.Button(input_box_frame, text="...", command=lambda : self.select_path(self.ei_config_i_path.set,filetype=("i files", "*.i")))
        self.select_config_i_path.pack(side='right',expand=False)          
        # end text view widget
        
        # button view widget
        self.label_frame_button = tkinter.LabelFrame(master, text="Button")
        self.label_frame_button.pack(side='top', fill='x', expand=False, padx=5, pady=5)
        
        self.bin_parse_button = tkinter.Button(self.label_frame_button, text="Parse BIN", command=self.button_parse_bin)
        self.bin_parse_button.grid(row=0,column=0)        
        
        self.bin_save_button = tkinter.Button(self.label_frame_button, text="Save BIN", command=self.button_save_bin)
        self.bin_save_button.grid(row=0,column=1)

        self.txt_save_button = tkinter.Button(self.label_frame_button, text="Save Text", command=self.button_save_txt)
        self.txt_save_button.grid(row=0,column=2)
        # end button view
        
    def __del__(self):
        print(self.get_current_info_path())
        properties.set("DEFAULT", "info_file_path", self.get_current_info_path())    
        with open('config.ini', "w") as f:
            properties.write(f)
            
    def select_path(self, set_path,filetype):
        print(filetype)
        path = filedialog.askopenfilename(title="Select file", filetypes=(filetype,("all files", "*.*")))
        print(path)
        set_path(path)
        return path
        
    def button_save_bin(self):
        if self.result_struct is None:
            tkinter.messagebox.showerror("ERROR", message = 'Please open bin file')
            return
        
        bin_file_data = filedialog.asksaveasfile(mode='wb',initialdir="./", title="Save file", filetypes=(("bin files", "*.bin"),("all files", "*.*")))
        if bin_file_data is None:
            return
        bin_file_data.write(self.result_struct)
        bin_file_data.close()

    def button_save_txt(self):
        if self.result_struct is None:
            tkinter.messagebox.showerror("ERROR", message = 'Please open bin file')
            return
        
        txt_file_data = filedialog.asksaveasfile(mode='w',initialdir="./", title="Save file", filetypes=(("txt files", "*.txt"),("all files", "*.*")))
        if txt_file_data is None:
            return
        txt_file_data.write(str(self.result_struct))
        txt_file_data.close()
    
    def button_parse_bin(self):
        self.parse_binary(self.bin_path.get())
    
    def get_current_info_path(self):
        return self.ei_config_i_path.get()

    def parse_binary(self, path):
        path=path.replace('{','') # {} is attached when path include space
        path=path.replace('}','')
        
        if os.path.isfile(path) is False:
            tkinter.messagebox.showerror('Error','There is no bin file in {} '.format(path))
            
        if (os.path.getsize(path) != 4096):
            tkinter.messagebox.showerror('Error','{} is not 4KB bin file'.format(path))
            return False

        if (self.bin_path.get() != path):
            self.bin_path.set(os.path.abspath(path))       
        # precondition setup.
        # gcc build for generating .i file
        if os.path.isfile(self.ei_config_i_path.get()) is False:
            tkinter.messagebox.showerror('Error','There is no .i file in {} '.format(self.ei_config_i_path.get()))
            # @24.04.03 gcc build no support
            
            #cur_project_path = self.project_path.get()
            #cur_project_path = os.path.abspath(cur_project_path)
            #print(cur_project_path)
            #include_dir = list(map(lambda _dir : os.path.abspath(os.path.join(cur_project_path,_dir)),cfg_include_path))
            #
            #for _dir in include_dir:
            #    if os.path.isdir(_dir) is False:
            #        tkinter.messagebox.showerror("ERROR", message = 'Can\'t find {} Please check repo directory'.format(_dir))            
            #        return
            #        
            #if os.path.isfile(os.path.join(os.getcwd(), 'main.i')) is False:        
            #    ret = os.system(r'gcc -v')
            #    if ret != 0:
            #        tkinter.messagebox.showerror("ERROR", message = 'Please install gcc')
            #        return
            #    gcc_cmd = r'gcc main.c -save-temps -I' + r' -I'.join(include_dir)          
            #    ret = os.system(gcc_cmd)
            #    if ret != 0:
            #        tkinter.messagebox.showerror("ERROR", message = 'Build failure. Please rebuild with {}'.format(gcc_cmd))
            #        os.system('del main.i')
            #        return            
            #i_file_path = os.path.join(os.getcwd(), 'main.i')
        else:
            i_file_path = self.ei_config_i_path.get()

        tkinter.messagebox.showinfo("INFO", message = "Use {}".format(i_file_path))
        self.view.delete(*self.view.get_children())            
        
        binary_file_handler = C2PyHandler.DefaultBinaryFileC2PyHandler(i_file_path,path)
        self.result_struct = binary_file_handler.convert(struct_declaration="EI_Config_t")
        
        s = recursive_tree(self.result_struct, self.view)

    def update_ei_struct_value(self,_name,_value):
        _name = _name[:-1] if _name[-1]=='.' else _name # if _name have ".", it shall be removed
        try:
            if eval('issubclass(type(self.result_struct.{}), ctypes.Array)'.format(_name)) is True:
                list_value = eval(_value)
                if (type(list_value) is not list):
                    tkinter.messagebox.showerror("ERROR", message = "Please input list type. e.g.) [1,2,3,4]")
                    return False

                if (type(list_value[0]) == list): #2-dimensional list. 
                    _x = len(list_value)
                    _y = len(list_value[0])
                    arr = ((ctypes.c_ubyte * _y)*_x)()
                    for xx in range(0,_x):
                        for yy in range(0,_y):
                            arr[xx][yy] = list_value[xx][yy]                    
                else:
                    arr = (ctypes.c_ubyte * len(list_value))(*list_value)
                cmd = 'self.result_struct.{} = arr'.format(_name)
                exec(cmd)
            else:
                cmd = 'self.result_struct.{} = {}'.format(_name,_value)
                exec(cmd)
            print('update complete: ', cmd)
            return True
        except Exception as e:
            tkinter.messagebox.showerror("ERROR", message = str(e))
            return False
            
if __name__ == '__main__':
    tk = TkinterDnD.Tk()
    tk.geometry('640x550')
    tk.title("pyBinParser")
    GUI(tk)
    tk.mainloop()
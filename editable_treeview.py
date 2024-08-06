from tkinter import ttk

import tkinter as tk

class PopupEntry(tk.Entry):
    def __init__(self, root, x, y, textvar,width = 10 ,entry_value='', text_justify = 'left', state='normal' ):
        super().__init__(root, relief = 'flat', justify = text_justify,bg='white', textvariable=textvar, state=state)
        self.place(x=x, y=y, width=width)
        
        self.textvar = textvar
        self.textvar.set(entry_value)
        self.focus_set()
        self.select_range(0, 'end')
        # move cursor to the end
        self.icursor('end')

        self.wait_var = tk.StringVar(master=self)
        self._bind_widget()

        self.entry_value = entry_value
        self.wait_window()
    
    def _bind_widget(self):
        self.bind("<Return>", self.retrive_value)
        self.bind('<FocusOut>', self.retrive_value)
        self.bind('<Escape>', self.cancel_value)

    def retrive_value(self, e):
        value = self.textvar.get()
        self.destroy()
        self.textvar.set(value)
    
    def cancel_value(self, e):
        self.destroy()
        self.textvar.set(self.entry_value)
        
class EditableTreeview(ttk.Treeview):
    def __init__(self, root, columns, bind_key,data:list, non_editable_columns = "",update_ei_struct_value=None,height=10):
        super().__init__(root, columns=columns,height=height)
        self.update_ei_struct_value = update_ei_struct_value
        self.root = root
        self.column_name = columns
        self.data = data
        self.bind_key = bind_key
        self.non_editable_columns = non_editable_columns

        self.set_primary_key_column_attributes()
        self.set_headings()
        self.insert_data()
        self.set_edit_bind_key()
    
    def set_primary_key_column_attributes(self):
        self.column("#0",width=100,stretch=1)

    def set_headings(self):
        for i in self.column_name:
            self.heading(column=i, text=i)

    def insert_data(self):
        for values in self.data:
            self.insert('', tk.END, values=values)
    
    def set_edit_bind_key(self):
        self.bind('<Double Button-1>', self.edit)
        self.bind('<F2>', self.edit)

    def get_absolute_x_cord(self):
        rootx = self.winfo_pointerx()
        widgetx = self.winfo_rootx()

        x = rootx - widgetx

        return x

    def get_absolute_y_cord(self):
        rooty = self.winfo_pointery()
        widgety = self.winfo_rooty()

        y = rooty - widgety

        return y
    
    def get_current_column(self):
        pointer = self.get_absolute_x_cord()
        return self.identify_column(pointer)

    def get_cell_cords(self,row,column):
        return self.bbox(row, column=column)
    
    def get_selected_cell_cords(self):
        row = self.focus()
        column = self.get_current_column()
        return self.get_cell_cords(row = row, column = column)

    def update_row(self, values, current_row, currentindex):
        #try:self.root.state()
        #except: return

        if (self.update_ei_struct_value(current_row,values) is True):
            self.set(current_row,'Values',values) # temporary code. TreeView columns shall be set "Values"
        
    def check_region(self):
        result = self.identify_region(x=(self.winfo_pointerx() - self.winfo_rootx()), y=(self.winfo_pointery()  - self.winfo_rooty()))
        print(result)
        if result == 'cell':return True
        else: return False

    def check_non_editable(self):
        if self.get_current_column() in self.non_editable_columns:return False
        else: return True

    def edit(self, e):
        editable = True
        if self.check_region() == False: 
            editable = False
            #return
        elif self.check_non_editable() == False:
            editable = False
            #return
        
        current_row = self.focus()
        currentindex = self.index(self.focus())
        if editable is True:
            current_row_values = list(self.item(self.focus(),'values'))
        else:
            current_row_values = self.item(self.focus(),'text')
        current_column = int(self.get_current_column().replace("#",''))-1
        if editable is True:
            current_cell_value = current_row_values[current_column]
        else:
            current_cell_value = current_row_values.strip()
        entry_cord = self.get_selected_cell_cords()
        entry_x = entry_cord[0]
        entry_y = entry_cord[1]
        entry_w = entry_cord[2]
        entry_h = entry_cord[3]

        entry_var = tk.StringVar()
        
        PopupEntry(self.root, x=entry_x, y=entry_y, width=entry_w,entry_value=current_cell_value, textvar= entry_var, text_justify='left', state='normal' if editable is True else 'readonly')
        if entry_var.get() != current_cell_value:
            if editable is True:
                current_row_values[current_column] = entry_var.get()
                self.update_row(values=current_row_values[current_column], current_row=current_row, currentindex=currentindex)
            
def demo():

    root = tk.Tk()
    root.title('Demo')
    root.geometry('620x200')
    
    columns = ('attribute', 'value', 'Broh')
    data = [('relx','6','7346347347'),('rely','1',24624623)]

    tree = EditableTreeview(root, columns=columns, bind_key='<Double-Button-1>',data=data, non_editable_columns="#1")
    tree.pack()

    # add a scrollbar
    scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack()
    
    # run the app
    root.mainloop()
            
    
    


if __name__ == '__main__':

    demo()
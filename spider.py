import tkinter
import requests
import logging
import threading
import webbrowser


from bs4 import BeautifulSoup
from requests import RequestException
from tkinter import messagebox
from tkinter import ttk


def logger_config():
    my_logger = logging.getLogger(__name__)
    errors_handler = logging.FileHandler('errors.log', mode='w')
    warnings_handler = logging.FileHandler('warnings.log', mode='w')

    errors_handler.setLevel(logging.ERROR)
    warnings_handler.setLevel(logging.WARNING)

    errors_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    warnings_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

    my_logger.addHandler(errors_handler)
    my_logger.addHandler(warnings_handler)

    return my_logger


logger = logger_config()


class SpiderTool(tkinter.Tk):
    __TOOL_NAME = 'Spider'
    __TOOL_SIZE = '700x400'
    __TOOL_BACKGROUND = '#d9d9d9'

    def __init__(self):
        super().__init__()
        self.title(self.__TOOL_NAME)
        self.geometry(self.__TOOL_SIZE)
        self.resizable(False, False)
        self.configure(background=self.__TOOL_BACKGROUND)

        # Url label and entry
        self.url_label = tkinter.Label(self, text='URL:', bg=self.__TOOL_BACKGROUND)
        self.url_label.place(x=180, y=10)
        self.url_entry = tkinter.Entry(self, width=50)
        self.url_entry.place(x=215, y=10)

        # Tag label and entry
        self.tag_label = tkinter.Label(self, text='Tag:', bg=self.__TOOL_BACKGROUND)
        self.tag_label.place(x=180, y=40)
        self.tag_entry = tkinter.Entry(self, width=50)
        self.tag_entry.place(x=215, y=40)

        # Create buttons
        self.__create_search_button()
        self.__create_links_button()
        self.__create_warnings_button()

        # Treeview with links
        self.__create_links_treeview()

        # Warnings
        self.__create_warnings_frame()

    # Create 3 buttons: Search, Links, Warnings
    def __create_search_button(self):
        self.search_button = tkinter.Button(self, text='Search', command=threading.Thread(target=self.__search).start)
        self.search_button.configure(width=10, height=1)
        self.search_button.place(x=225, y=70)

    def __create_links_button(self):
        self.treeview_show_button = tkinter.Button(self, text='Links', command=self.__show_treeview)
        self.treeview_show_button.configure(width=10, height=1)
        self.treeview_show_button.place(x=325, y=70)

    def __create_warnings_button(self):
        self.warnings_button = tkinter.Button(self, text='Warnings', command=self.__hide_treeview)
        self.warnings_button.configure(width=10, height=1)
        self.warnings_button.place(x=425, y=70)

    # Method used by warnings button to hide treeview and display warnings widget
    def __hide_treeview(self):
        self.tree.place_forget()
        self.vsb.place_forget()
        self.warnings.place(x=10, y=105)

    # Method used by links button to hide warnings widget and display treeview with links
    def __show_treeview(self):
        self.tree.place(x=10, y=105)
        self.vsb.place(x=675, y=105, height=286)
        self.warnings.place_forget()

    # Text frame in which will be displayed all warnings during searching
    def __create_warnings_frame(self):
        self.warnings = tkinter.Text(self, width=84, height=17)
        self.warnings.place(x=15, y=105)
        self.warnings.place_forget()

    # Treeview in which links are shown
    def __create_links_treeview(self):
        self.tree = tkinter.ttk.Treeview(master=self,
                                         columns=('id', 'link', 'size', 'type'),
                                         show='headings',
                                         )
        self.tree.column('id', width=30, anchor='center')
        self.tree.column('link', width=400)
        self.tree.column('size', width=90, anchor='center')
        self.tree.column('type', width=140, anchor='center')

        self.tree.heading('id', text='ID')
        self.tree.heading('link', text='Link')
        self.tree.heading('size', text='Size (KB)', anchor='center')
        self.tree.heading('type', text='Type', anchor='center')

        self.tree.place(x=10, y=105)
        self.tree.bind('<Double-1>', self.__open_link)

        style = tkinter.ttk.Style()
        style.configure('Treeview', rowheight=26)

        # Scrollbar
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.vsb.place(x=675, y=105, height=286)
        self.tree.configure(yscrollcommand=self.vsb.set)

    # Utility method to open links from treeview
    def __open_link(self, event):
        item = self.tree.identify('item', event.x, event.y)
        link = self.tree.item(item, 'values')[1]
        webbrowser.open(link)

    # Main method of tool which search for links in a given URL and display valid links into treeview
    def __search_links(self, url: str, tag: str):
        try:
            req = requests.get(url)
            url_html = BeautifulSoup(req.text, 'html.parser')
            link_index = 0
            tag_found = 0
            for a_element in url_html.find_all('a', href=True):
                # check if <a></a> contains specified tag
                if a_element.get(tag):
                    my_link = a_element.get('href')
                    # check if the link in <a></a> is valid
                    try:
                        tag_found = 1
                        link_req = requests.get(my_link)
                        # link is valid if his status code is 200
                        if link_req.status_code == 200:
                            info = requests.head(my_link)
                            link_size_and_type = []

                            # if 'content-length' header is present, save link size in KB, otherwise set his size to 0
                            if 'content-length' in info.headers:
                                if int(info.headers['content-length']) == 0:
                                    link_size_and_type.append(0)
                                else:
                                    link_size_and_type.append(
                                        float("{:.2f}".format(int(info.headers['content-length']) / 1024)))
                            else:
                                link_size_and_type.append(0)

                            # if 'content-type' header is present, save link type, otherwise set his type to 'Unknown'
                            if 'content-type' in info.headers:
                                link_size_and_type.append(info.headers['content-type'])
                            else:
                                link_size_and_type.append('Unknown')

                            if link_index == 0:
                                self.tree.delete(*self.tree.get_children())

                            self.tree.insert('', 'end', values=(link_index,
                                                                my_link,
                                                                link_size_and_type[0],
                                                                link_size_and_type[1])
                                             )
                            link_index += 1
                    except RequestException as e:
                        logger.warning(e)
                        self.warnings.insert(tkinter.END, "WARNING - Invalid link inside <a></a> tag!\n")
                        self.warnings.insert(tkinter.END, f"        - Link: {my_link}\n")

            # If tag is not found through valid <a></a> elements, a message is displayed into treeview
            if tag_found == 0:
                logger.error("Tag was not found!")
                self.tree.delete(*self.tree.get_children())
                self.tree.insert('', 'end', values=('', 'Tag not found!', '', ''))

        except RequestException as e:
            logger.warning(e)
            self.tree.delete(*self.tree.get_children())
            self.tree.insert('', 'end', values=('', 'Invalid URL!', '', ''))
            self.warnings.insert(tkinter.END, "WARNING - Invalid URL!\n")
            self.warnings.insert(tkinter.END, f"      - Given URL: {url}\n")

    # Method called by search button
    def __search(self):
        url = self.url_entry.get()
        tag = self.tag_entry.get()
        if url and tag:
            self.tree.delete(*self.tree.get_children())
            self.tree.insert('', 'end', values=('', 'Searching...', '', ''))
            self.search_button['state'] = 'disabled'
            self.__search_links(url, tag)
            self.search_button.destroy()
            self.__create_search_button()
        else:
            tkinter.messagebox.showerror('Error', 'URL and Tag are required')
            logger.error("Invalid given input!")
            self.search_button.destroy()
            self.__create_search_button()

    # Run method of tool
    def run_spider(self):
        self.mainloop()


if __name__ == '__main__':
    app = SpiderTool()
    app.run_spider()
